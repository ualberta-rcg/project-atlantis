# Plan from the beginning (v3)

## What we do

We scan **deserts** with Sentinel-1 radar to find **candidate locations** where structures may be buried. **One Git repo** holds config, tracking, and results. Jobs clone the repo, **claim tiles** (by tile_id only), **fetch imagery once per tile**, then **run all enabled scan types** on that data (temporal variance, CV, MAD, backscatter intensity, etc.). No separate database.

## Design: fetch once, analyze many

Fetching from the CDSE API is slow and rate-limited. Running many analyses on the same fetched data is cheap (seconds of CPU). So each job:

1. Claims one or more **tiles** (rectangles from the target list).
2. For each tile: **fetch** 8–15 S1 images (same bbox, same pixel size) **once**.
3. **Build stack** once: mean, var, std, median for VV and VH (8-band stack).
4. **Run every enabled scan type** from `config/scan.json` on that stack (each writes to `results/<tile_id>/<scan_type>/`).
5. Append to **processed_tiles.jsonl** (v3 schema: tile_id, scan_types_run, candidates_by_type, images_used, runtime_seconds).
6. **Push** with retry (pull --rebase + jitter).

## What lives in the repo

| What | Where |
|------|--------|
| Master config | `config/scan.json` (regions, tile_defaults, scan_types, composite_scores, job_defaults) |
| Tile list | `config/target_tiles.json` (from `generate_target_tiles.py --from-scan`) |
| Which tiles done | `processed_tiles.jsonl` (append-only) |
| Which tiles claimed | `claimed_tiles.jsonl` (append-only, TTL) |
| Per-tile results | `results/<tile_id>/stack.tif`, `results/<tile_id>/<scan_type>/` (anomaly.tif, candidates, metadata) |
| All candidates | `results/all_candidates.geojson` (rebuilt by `rebuild_aggregate.py`) |

## Scan types (from scan.json)

Enabled scan types run on every tile after the stack is built. Examples: **temporal_variance_95**, **temporal_variance_99**, **backscatter_intensity** (reference map, no candidates). More can be added in scan.json and in `scripts/scan_types/<name>.py`. Resolution: 10 m/pixel (max useful for IW GRD). Tile size: 25×25 km default.

## Job flow

1. Clone repo; read scan.json, target_tiles.json, processed_tiles.jsonl, claimed_tiles.jsonl.
2. Pick available tiles (not in processed, not actively claimed or claim expired).
3. Claim a batch; append to claimed_tiles.jsonl; push (retry on failure).
4. For each claimed tile: fetch → build_stack → run all enabled scan types → write process_record → append processed_tiles.jsonl.
5. Push results.

## Env vars

- **REPO_URL** — Git clone URL (with auth for push).
- **CDSE_CLIENT_ID**, **CDSE_CLIENT_SECRET** — CDSE Process API.
- **GIT_SSH_COMMAND** — Optional; for SSH deploy key.
- **BATCH_SIZE**, **CLUSTER_ID** — Optional.

## Quick start

```bash
python scripts/generate_target_tiles.py --from-scan
python scripts/run_pipeline.py --batch-size 1
```

Full v3 plan: **.cursor/plans/Archaeology scan full repo and process record-0babcd0b.plan.md**
