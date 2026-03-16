# Archaeology Radar Scan (v3)

Scan deserts and high-potential areas with Sentinel-1 radar to find candidate locations where structures may be buried. **Fetch once per tile, run all enabled scan types** (temporal variance, CV, MAD, backscatter intensity, etc.). Config, tracking, and results live in one Git repo; jobs clone, claim tiles, process, and push.

## Config

- **config/scan.json** — Master config: scan_regions, tile_defaults, imagery settings, scan_types (each with name, enabled, score_formula, threshold_percentile), composite_scores, job_defaults.
- **config/target_tiles.json** — Generated from scan.json: `python scripts/generate_target_tiles.py --from-scan`
- Or generate for a region: `python scripts/generate_target_tiles.py --min-lon 25 --max-lon 30 --min-lat 22 --max-lat 27 --size-km 25 -o config/target_tiles.json`

## Run

```bash
export CDSE_CLIENT_ID=... CDSE_CLIENT_SECRET=...
export REPO_URL=...   # for push (optional for local test)

# Generate tiles from scan.json regions
python scripts/generate_target_tiles.py --from-scan

# Single-tile test (no claim)
python scripts/run_pipeline.py qubbet_el_hawa

# Claim batch, fetch once per tile, run all scan types, push
python scripts/run_pipeline.py --batch-size 1
```

## v3 pipeline

1. Claim tiles (by tile_id only) from target_tiles.json; append to claimed_tiles.jsonl; push.
2. For each claimed tile: **fetch** imagery once → **build_stack** (mean/var/std/median VV+VH) → **run each enabled scan type** from scan.json → write process_record; append to processed_tiles.jsonl; push.

Tracking: **processed_tiles.jsonl**, **claimed_tiles.jsonl** (append-only JSONL, TTL on claims). Aggregate: `python scripts/rebuild_aggregate.py` rebuilds all_candidates.geojson from results.

## Slurm

```bash
export REPO_URL=... CDSE_CLIENT_ID=... CDSE_CLIENT_SECRET=...
sbatch --array=0-99 slurm/submit_array.sh
```

## Services and env

See **docs/SERVICES_AND_ENV.md**. Required: `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET`. For push: `REPO_URL` (with auth). Optional: `GIT_SSH_COMMAND`, `BATCH_SIZE`, `CLUSTER_ID`.

## Plan

Full v3 plan: **.cursor/plans/Archaeology scan full repo and process record-0babcd0b.plan.md**
