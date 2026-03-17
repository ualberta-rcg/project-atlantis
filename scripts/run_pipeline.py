#!/usr/bin/env python3
"""
Run archaeology pipeline (v3): claim TILES, fetch once per tile,
build stack once, run ALL enabled scan types, generate PNGs, copy to repo, push.

Supports --workdir for processing in a temp directory before copying to repo.

Usage:
  export REPO_URL=... CDSE_CLIENT_ID=... CDSE_CLIENT_SECRET=...
  python run_pipeline.py tile_30.8740_29.2470                 # single-tile, process in repo
  python run_pipeline.py tile_30.8740_29.2470 --workdir /tmp  # single-tile, process in /tmp
  python run_pipeline.py --batch-size 1                       # claim-based batch
"""
import os
import sys
import json
import shutil
import subprocess
import time
import random
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
PROCESSED_PATH = os.path.join(PROJECT_ROOT, "processed_tiles.jsonl")
CLAIMED_PATH = os.path.join(PROJECT_ROOT, "claimed_tiles.jsonl")
TARGET_TILES_PATH = os.path.join(CONFIG_DIR, "target_tiles.json")
SCAN_CONFIG_PATH = os.path.join(CONFIG_DIR, "scan.json")

sys.path.insert(0, SCRIPT_DIR)


def run(cmd, check=True, cwd=None):
    cwd = cwd or PROJECT_ROOT
    print(f"[run] {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=cwd)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(cmd)}")
    return r.returncode


def read_jsonl(path):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def append_jsonl(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def get_worker_id():
    slurm_id = os.environ.get("SLURM_JOB_ID")
    if slurm_id:
        return f"slurm-{slurm_id}"
    return os.environ.get("WORKER_ID") or f"{os.uname().nodename}-{os.getpid()}"


def load_target_tiles():
    if not os.path.isfile(TARGET_TILES_PATH):
        return []
    with open(TARGET_TILES_PATH) as f:
        return json.load(f)


def load_scan_config():
    if not os.path.isfile(SCAN_CONFIG_PATH):
        return {}
    with open(SCAN_CONFIG_PATH) as f:
        return json.load(f)


def get_enabled_scan_types(scan_config):
    return [s for s in scan_config.get("scan_types", []) if s.get("enabled", True)]


def pick_work_v3(target_tiles, processed_records, claimed_records, batch_size, ttl_minutes):
    now = datetime.utcnow()
    done_set = {r["tile_id"] for r in processed_records}
    active_claims = set()
    for r in claimed_records:
        try:
            claimed_at = datetime.fromisoformat(r["claimed_at"].replace("Z", "+00:00"))
        except Exception:
            continue
        ttl = r.get("ttl_minutes", ttl_minutes)
        if claimed_at + timedelta(minutes=ttl) > now:
            active_claims.add(r["tile_id"])
    available = [t for t in target_tiles if t["tile_id"] not in done_set and t["tile_id"] not in active_claims]
    random.shuffle(available)
    return available[:batch_size]


def push_with_retry(max_retries=10):
    for attempt in range(1, max_retries + 1):
        run(["git", "add", "results/", "processed_tiles.jsonl", "claimed_tiles.jsonl"], check=False)
        run(["git", "commit", "-m", f"Results: worker {get_worker_id()} @ {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}"], check=False)
        r = subprocess.run(["git", "push"], cwd=PROJECT_ROOT)
        if r.returncode == 0:
            print("[push] Success.", flush=True)
            return True
        jitter = random.randint(1, 15)
        print(f"[push] Failed, pull --rebase and retry in {jitter}s (attempt {attempt}/{max_retries})", flush=True)
        time.sleep(jitter)
        run(["git", "pull", "--rebase"], check=False)
    print("ERROR: push failed after retries", file=sys.stderr, flush=True)
    return False


def generate_pngs(tile_dir):
    try:
        from generate_pngs import generate_all_pngs
        n = generate_all_pngs(tile_dir)
        print(f"[png] Generated {n} previews in {tile_dir}", flush=True)
        return n
    except Exception as e:
        print(f"[png] Warning: {e}", file=sys.stderr, flush=True)
        return 0


def process_one_tile_v3(tile, scan_config, worker_id, workdir=None):
    """
    Fetch once, build stack, run all enabled scan types.
    If workdir is set, process there then copy to repo results/.
    """
    tile_id = tile["tile_id"]
    bbox = tile["bbox"]
    td = scan_config.get("tile_defaults", {})
    size_km = tile.get("size_km") or td.get("size_km", 5)
    res_m = tile.get("resolution_m") or td.get("resolution_m", 10)
    size_px = int(size_km * 1000 / res_m) if size_km and res_m else 500
    enabled = get_enabled_scan_types(scan_config)
    if not enabled:
        enabled = [{"name": "temporal_variance_99", "threshold_percentile": 99, "score_formula": "var_VV + var_VH"}]

    # Determine working directory
    if workdir:
        work_base = os.path.join(workdir, f"atlantis_{get_worker_id()}")
        out_dir = os.path.join(work_base, tile_id)
    else:
        out_dir = os.path.join(RESULTS_DIR, tile_id)

    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    t0 = time.time()

    # ---- FETCH ----
    print(f"\n{'='*60}", flush=True)
    print(f"[tile] {tile_id}  bbox={bbox}  {size_px}x{size_px}px", flush=True)
    print(f"[tile] Working in: {out_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)

    fetch_base = os.path.dirname(out_dir)
    try:
        from sites import SITES
        if tile_id in SITES:
            run([sys.executable, os.path.join(SCRIPT_DIR, "fetch_s1_site.py"),
                 tile_id, "--data-dir", fetch_base, "--size", str(size_px)])
        else:
            run([sys.executable, os.path.join(SCRIPT_DIR, "fetch_s1_tile.py"),
                 tile_id, "--bbox", *map(str, bbox),
                 "--data-dir", fetch_base, "--size", str(size_px)])
    except ImportError:
        run([sys.executable, os.path.join(SCRIPT_DIR, "fetch_s1_tile.py"),
             tile_id, "--bbox", *map(str, bbox),
             "--data-dir", fetch_base, "--size", str(size_px)])

    tifs = sorted([os.path.join(raw_dir, f) for f in os.listdir(raw_dir)
                   if f.endswith(".tif") and f.startswith("s1_")])
    if not tifs:
        raise RuntimeError(f"No GeoTIFFs after fetch for {tile_id}")
    images_used = len(tifs)
    print(f"[fetch] {images_used} images downloaded", flush=True)

    # ---- BUILD STACK ----
    stack_path = os.path.join(out_dir, "stack.tif")
    run([sys.executable, os.path.join(SCRIPT_DIR, "build_stack.py"), "-o", stack_path] + tifs)

    # ---- RUN SCAN TYPES ----
    candidates_by_type = {}
    scan_types_run = []
    for st in enabled:
        name = st.get("name", "")
        if not name:
            continue
        scan_out = os.path.join(out_dir, name)
        rc = run([sys.executable, os.path.join(SCRIPT_DIR, "run_scan_type.py"),
                  stack_path, name, scan_out, tile_id],
                 check=(st.get("score_formula") is not None))
        scan_types_run.append(name)
        meta_path = os.path.join(scan_out, "metadata.json")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            candidates_by_type[name] = meta.get("num_candidates", meta.get("candidate_count", 0))
        else:
            cand_path = os.path.join(scan_out, "candidates.geojson")
            if os.path.isfile(cand_path):
                with open(cand_path) as f:
                    candidates_by_type[name] = len(json.load(f).get("features", []))
            else:
                candidates_by_type[name] = 0
        print(f"[scan] {name}: {candidates_by_type[name]} candidates", flush=True)

    runtime_seconds = round(time.time() - t0, 2)
    combined_top5 = candidates_by_type.get("combined_top5", candidates_by_type.get("temporal_variance_99", 0))

    # ---- PROCESS RECORD ----
    with open(os.path.join(out_dir, "process_record.json"), "w") as f:
        json.dump({
            "tile_id": tile_id,
            "inputs": {"bbox": bbox, "resolution_m": res_m, "size_px": [size_px, size_px], "image_count": images_used},
            "coregistration": {"method": "api_reprojection", "note": "Same bbox and dimensions from CDSE Process API."},
            "scan_types_run": {name: {"candidates": candidates_by_type.get(name, 0)} for name in scan_types_run},
            "run_metadata": {
                "worker_id": worker_id,
                "cluster_id": os.environ.get("CLUSTER_ID"),
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                "timestamp_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "runtime_seconds": runtime_seconds,
            },
        }, f, indent=2)

    # ---- GENERATE PNGs ----
    generate_pngs(out_dir)

    # ---- GENERATE FINAL REPORT ----
    try:
        from tile_report import generate_report
        n_ranked = generate_report(out_dir)
        print(f"[report] {n_ranked} ranked candidates in final report", flush=True)
    except Exception as e:
        print(f"[report] Warning: {e}", file=sys.stderr, flush=True)

    # ---- COPY TO REPO (if using workdir) ----
    if workdir:
        repo_out = os.path.join(RESULTS_DIR, tile_id)
        print(f"[copy] {out_dir} -> {repo_out}", flush=True)
        if os.path.exists(repo_out):
            shutil.rmtree(repo_out)
        shutil.copytree(out_dir, repo_out)
        print(f"[copy] Done. Cleaning workdir.", flush=True)
        shutil.rmtree(out_dir, ignore_errors=True)

    print(f"\n[done] {tile_id}: {runtime_seconds}s, {images_used} images, {len(scan_types_run)} scan types", flush=True)
    return candidates_by_type, scan_types_run, images_used, runtime_seconds, combined_top5


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Run archaeology pipeline v3")
    ap.add_argument("tile_id", nargs="?", default=None, help="Single tile_id for testing")
    ap.add_argument("--batch-size", type=int, default=5)
    ap.add_argument("--claim-ttl", type=int, default=180)
    ap.add_argument("--workdir", default=None,
                    help="Temp directory for processing (e.g. /tmp). Results copied to repo when done.")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()

    scan_config = load_scan_config()
    job_defaults = scan_config.get("job_defaults", {})
    batch_size = args.batch_size or job_defaults.get("batch_size", 5)
    ttl_minutes = args.claim_ttl or job_defaults.get("claim_ttl_minutes", 180)
    worker_id = get_worker_id()

    # Single-tile mode
    if args.tile_id:
        target_tiles = load_target_tiles()
        tile = next((t for t in target_tiles if t["tile_id"] == args.tile_id), None)
        if not tile:
            try:
                from sites import SITES
                if args.tile_id in SITES:
                    tile = {"tile_id": args.tile_id, "bbox": SITES[args.tile_id]["bbox"]}
            except ImportError:
                pass
        if not tile:
            print(f"Tile {args.tile_id} not in target_tiles or sites.", file=sys.stderr)
            sys.exit(1)

        candidates_by_type, scan_types_run, images_used, runtime_seconds, combined_top5 = \
            process_one_tile_v3(tile, scan_config, worker_id, workdir=args.workdir)

        append_jsonl(PROCESSED_PATH, {
            "tile_id": tile["tile_id"],
            "timestamp_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "worker_id": worker_id,
            "images_used": images_used,
            "runtime_seconds": runtime_seconds,
            "scan_types_run": scan_types_run,
            "candidates_by_type": candidates_by_type,
            "combined_top5_candidates": combined_top5,
        })
        if not args.no_push:
            push_with_retry()
        return

    # Claim-based batch mode
    target_tiles = load_target_tiles()
    if not target_tiles:
        print("No target_tiles.json or empty. Run generate_target_tiles.py.", file=sys.stderr)
        sys.exit(1)

    # Pull latest tracking before claiming
    run(["git", "pull", "--rebase"], check=False)

    processed = read_jsonl(PROCESSED_PATH)
    claimed = read_jsonl(CLAIMED_PATH)
    batch = pick_work_v3(target_tiles, processed, claimed, batch_size, ttl_minutes)
    if not batch:
        print("No work available — all tiles done or claimed.")
        return

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for t in batch:
        append_jsonl(CLAIMED_PATH, {
            "tile_id": t["tile_id"], "claimed_at": now_iso,
            "ttl_minutes": ttl_minutes, "worker_id": worker_id,
        })
    if not args.no_push and not push_with_retry():
        sys.exit(1)

    for tile in batch:
        try:
            candidates_by_type, scan_types_run, images_used, runtime_seconds, combined_top5 = \
                process_one_tile_v3(tile, scan_config, worker_id, workdir=args.workdir)
            append_jsonl(PROCESSED_PATH, {
                "tile_id": tile["tile_id"],
                "timestamp_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "worker_id": worker_id,
                "images_used": images_used,
                "runtime_seconds": runtime_seconds,
                "scan_types_run": scan_types_run,
                "candidates_by_type": candidates_by_type,
                "combined_top5_candidates": combined_top5,
            })
            if not args.no_push:
                push_with_retry()
        except Exception as e:
            print(f"FAILED {tile['tile_id']}: {e}", file=sys.stderr, flush=True)

    print(f"\nBatch done. {len(batch)} tiles processed.", flush=True)


if __name__ == "__main__":
    main()
