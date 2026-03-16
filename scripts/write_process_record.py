#!/usr/bin/env python3
"""
Write process_record.json (and optional .md) for a pipeline run.
Schema: see plan section 2 (inputs, steps, coregistration, detection, outputs, run_metadata).
"""
import json
import os
import sys

try:
    import rasterio
except ImportError:
    rasterio = None


def get_raster_info(path):
    """Return crs, bounds, transform, res (pixel size) from a GeoTIFF."""
    if not rasterio or not os.path.isfile(path):
        return None
    with rasterio.open(path) as src:
        bounds = list(src.bounds)
        res = (float(src.res[0]), float(src.res[1]))
        return {
            "crs": str(src.crs) if src.crs else None,
            "bounds": bounds,
            "transform": list(src.transform)[:6] if src.transform else None,
            "width": src.width,
            "height": src.height,
            "res": res,
        }


def write_process_record(
    out_dir,
    tile_id,
    pathway,
    bbox,
    date_range,
    time_windows,
    size_px,
    steps,
    threshold_percentile=95,
    score_band="var_VV + var_VH",
    chance_formula="(score - thresh) / (max_score - thresh)",
    stack_path=None,
    anomaly_path=None,
    candidates_geojson_path=None,
    candidates_csv_path=None,
    candidate_count=0,
    coherence_path=None,
    displacement_los_path=None,
    runtime_seconds=None,
    cluster=None,
    git_commit=None,
):
    """
    Write results/<tile_id>/<pathway>/process_record.json and optionally process_record.md.
    Coregistration for default (API) pathway: same bbox/size from CDSE Process API.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Reference grid from stack if available
    raster_info = get_raster_info(stack_path) if stack_path else None
    if raster_info:
        coreg = {
            "method": "CDSE Process API same bbox/size",
            "crs": raster_info["crs"],
            "bounds": raster_info["bounds"],
            "pixel_size": list(raster_info["res"]),
            "transform_affine": raster_info["transform"],
            "resampling": None,
            "dem_path": None,
            "note": "All inputs aligned to same grid from API; no warp applied.",
        }
    else:
        coreg = {
            "method": "CDSE Process API same bbox/size",
            "crs": "EPSG:4326",
            "bounds": bbox if len(bbox) == 4 else None,
            "pixel_size": None,
            "transform_affine": None,
            "resampling": None,
            "dem_path": None,
            "note": "Same bbox/size from CDSE Process API; no warp applied.",
        }

    record = {
        "inputs": {
            "bbox": bbox,
            "date_range": list(date_range) if date_range else None,
            "source": "CDSE Process API",
            "time_windows": time_windows,
            "resolution_m": None,
            "size_px": size_px,
        },
        "steps": steps,
        "coregistration": coreg,
        "detection": {
            "score_band": score_band,
            "threshold_percentile": threshold_percentile,
            "chance_formula": chance_formula,
        },
        "outputs": {
            "stack": stack_path,
            "anomaly": anomaly_path,
            "candidates_geojson": candidates_geojson_path,
            "candidates_csv": candidates_csv_path,
            "candidate_count": candidate_count,
            "coherence": coherence_path,
            "displacement_los": displacement_los_path,
        },
        "run_metadata": {
            "cluster": cluster or os.environ.get("CLUSTER_ID", "unknown"),
            "timestamp_iso": None,  # caller can set
            "git_commit": git_commit,
            "runtime_seconds": runtime_seconds,
        },
    }

    json_path = os.path.join(out_dir, "process_record.json")
    with open(json_path, "w") as f:
        json.dump(record, f, indent=2)
    print(f"Wrote {json_path}")

    # Optional human-readable summary
    md_path = os.path.join(out_dir, "process_record.md")
    with open(md_path, "w") as f:
        f.write(f"# Process record: {tile_id} / {pathway}\n\n")
        f.write(f"- **Steps:** {', '.join(steps)}\n")
        f.write(f"- **Coregistration:** {coreg['method']}\n")
        f.write(f"- **Detection:** percentile={threshold_percentile}, score={score_band}\n")
        f.write(f"- **Candidates:** {candidate_count}\n")
        if record["run_metadata"]["runtime_seconds"] is not None:
            f.write(f"- **Runtime:** {record['run_metadata']['runtime_seconds']} s\n")
    print(f"Wrote {md_path}")
    return json_path


def _git_commit():
    try:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
    except Exception:
        pass
    return None


if __name__ == "__main__":
    ap = __import__("argparse").ArgumentParser(description="Write process_record.json for a run")
    ap.add_argument("out_dir", help="Output directory (e.g. results/<tile_id>/<pathway>)")
    ap.add_argument("--tile-id", required=True)
    ap.add_argument("--pathway", required=True)
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("min_lon", "min_lat", "max_lon", "max_lat"), required=True)
    ap.add_argument("--date-range", nargs=2, metavar=("start", "end"), default=None)
    ap.add_argument("--time-windows", type=str, nargs="+", default=None, help="flat list: start end start end ...")
    ap.add_argument("--size-px", type=int, nargs=2, default=[512, 512])
    ap.add_argument("--steps", nargs="+", default=["fetch_s1", "stack_timeseries", "detect_anomalies"])
    ap.add_argument("--percentile", type=float, default=95)
    ap.add_argument("--stack", default=None)
    ap.add_argument("--anomaly", default=None)
    ap.add_argument("--candidates-geojson", default=None)
    ap.add_argument("--candidates-csv", default=None)
    ap.add_argument("--candidate-count", type=int, default=0)
    ap.add_argument("--runtime", type=float, default=None)
    ap.add_argument("--cluster", default=None)
    args = ap.parse_args()

    time_windows = None
    if args.time_windows and len(args.time_windows) >= 2:
        time_windows = [tuple(args.time_windows[i:i+2]) for i in range(0, len(args.time_windows), 2)]

    write_process_record(
        args.out_dir,
        tile_id=args.tile_id,
        pathway=args.pathway,
        bbox=args.bbox,
        date_range=args.date_range or [],
        time_windows=time_windows or [],
        size_px=args.size_px,
        steps=args.steps,
        threshold_percentile=args.percentile,
        stack_path=args.stack,
        anomaly_path=args.anomaly,
        candidates_geojson_path=args.candidates_geojson,
        candidates_csv_path=args.candidates_csv,
        candidate_count=args.candidate_count,
        runtime_seconds=args.runtime,
        cluster=args.cluster,
        git_commit=_git_commit(),
    )
