# Archaeology Radar Scan (v3)

Scan deserts and high-potential areas with Sentinel-1 radar to find candidate locations where structures or objects may be buried. The pipeline fetches radar images, stacks them over time, and runs every available analysis on that data to detect anomalies.

**Design principle: fetch once, analyze many ways.** Fetching imagery from the CDSE API is the slow and expensive step. Running 10+ different analyses on the fetched data costs seconds of CPU time and zero API calls. The pipeline fetches imagery once per tile and runs ALL enabled scan types on it.

Everything -- config, tracking, results, images -- lives in this Git repo. No database. Jobs clone the repo, do work, and push results back.

## Quick start

```bash
# 1. Clone
git clone git@github.com:ualberta-rcg/project-atlantis.git && cd project-atlantis

# 2. Set env (or add to ~/.bashrc)
export CDSE_CLIENT_ID="your-id"
export CDSE_CLIENT_SECRET="your-secret"
export GIT_SSH_COMMAND="ssh -i ~/.ssh/archaeology-deploy-key -o StrictHostKeyChecking=accept-new"
export REPO_URL="git@github.com:ualberta-rcg/project-atlantis.git"

# 3. Generate tiles
python scripts/generate_target_tiles.py --from-scan

# 4. Test one tile (all scan types)
python scripts/run_pipeline.py --batch-size 1

# 5. Check results
cat processed_tiles.jsonl
ls results/tile_*/combined_top5/candidates.geojson

# 6. Scale
sbatch --array=0-99 slurm/submit_array.sh
```

## Config

- **config/scan.json** -- Master config: scan_regions, tile_defaults (5 km, 10 m, 500x500 px), imagery (8-15 images), all scan_types (15 defined, 12 enabled by default), composite_scores, api_limits, job_defaults.
- **config/target_tiles.json** -- Generated from scan.json: `python scripts/generate_target_tiles.py --from-scan`

## v3 pipeline (per tile)

1. **Fetch** imagery once (12 S1 GRD images, same bbox, 500x500 px at 10 m/pixel, ~102 s/image)
2. **Build stack** once (mean/var/std/median VV+VH -> stack.tif)
3. **Run all enabled scan types** on that stack (each writes to `results/<tile_id>/<scan_type>/`)
4. **Compute composite scores** (combined_top5: multi-method agreement)
5. **Write process record**, append to processed_tiles.jsonl, push

## Scan types (12 enabled by default)

| Category | Scan types |
|----------|-----------|
| Temporal | temporal_variance_95, temporal_variance_99, temporal_cv, temporal_mad, seasonal_difference, multitemporal_change |
| Polarimetric | crosspol_ratio, crosspol_ratio_variance |
| Spatial | texture_glcm, edge_detection, spatial_autocorrelation |
| Baseline | backscatter_intensity (reference map, no candidates) |
| Disabled | coherence_coh12 (extra API), insar_displacement (SLC+ISCE2), ml_detector (placeholder) |

## Job coordination

Jobs claim **tiles** (not tile+scan_type). Tracking via append-only JSONL files with TTL on claims. Push with retry (pull --rebase + jitter). Multiple clusters self-coordinate through the same repo.

## Env vars

| Variable | Required | Description |
|----------|----------|-------------|
| `REPO_URL` | Yes | `git@github.com:ualberta-rcg/project-atlantis.git` |
| `CDSE_CLIENT_ID` | Yes | CDSE OAuth client ID |
| `CDSE_CLIENT_SECRET` | Yes | CDSE OAuth client secret |
| `GIT_SSH_COMMAND` | Yes | `ssh -i ~/.ssh/archaeology-deploy-key -o StrictHostKeyChecking=accept-new` |
| `BATCH_SIZE` | No | Tiles per claim (default: 5) |
| `CLUSTER_ID` | No | For logging |
| `SCRATCH_DIR` | No | Raw image storage (default: `$TMPDIR`) |

## Repo layout

```
project-atlantis/
├── config/
│   ├── scan.json               <- THE master config
│   ├── target_tiles.json       <- generated from scan.json
│   └── sites.json              <- optional named sites
├── scripts/
│   ├── run_pipeline.py         <- claim -> fetch -> run all scan types -> push
│   ├── fetch_s1_tile.py        <- fetch S1 imagery
│   ├── build_stack.py          <- temporal stack (shared base)
│   ├── run_scan_type.py        <- dispatcher
│   ├── generate_target_tiles.py
│   ├── rebuild_aggregate.py
│   └── scan_types/             <- one script per scan type
├── results/
│   ├── all_candidates.geojson
│   └── <tile_id>/
│       ├── stack.tif
│       ├── process_record.json
│       └── <scan_type>/        <- anomaly.tif, candidates.geojson, metadata.json
├── processed_tiles.jsonl       <- append-only tracking
├── claimed_tiles.jsonl         <- append-only claims with TTL
└── slurm/
    ├── submit_array.sh
    └── job_wrapper.sh
```

## Adding a new scan type

1. Define it in `config/scan.json` under `scan_types`
2. Write `scripts/scan_types/your_new_type.py` with `run(stack_path, images_dir, output_dir, config)`
3. Run `python scripts/add_scan_type.py --scan-type your_new_type` on existing tiles (no re-fetch)
4. Push results
