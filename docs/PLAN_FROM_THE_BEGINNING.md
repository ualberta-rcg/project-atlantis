# Plan from the beginning (v3)

## What we do

Scan deserts with Sentinel-1 radar to find candidate locations where structures may be buried. One Git repo (`git@github.com:ualberta-rcg/project-atlantis.git`) holds config, tracking, and results. Jobs clone the repo, claim tiles, fetch imagery once per tile, run all enabled scan types, and push results back. No database.

## Design: fetch once, analyze many

Fetching from the CDSE API is slow (minutes per tile, rate-limited). Running 12 analyses on the same data is cheap (seconds of CPU). So each job:

1. Claims tiles (by tile_id only) from `config/target_tiles.json`.
2. For each tile: fetches 8-15 S1 images (same bbox, 500x500 px at 10 m) once.
3. Builds stack once: mean, var, std, median for VV and VH (8-band `stack.tif`).
4. Runs every enabled scan type from `config/scan.json` on that stack.
5. Appends to `processed_tiles.jsonl` (tile_id, scan_types_run, candidates_by_type, images_used).
6. Pushes with retry (pull --rebase + jitter).

## Resolution and tile size

10 m/pixel -- the maximum useful resolution from Sentinel-1 IW GRD. Tiles are **5x5 km = 500x500 pixels** (practical limit on free CDSE tier; 25 km / 2500 px times out). Preferred 12 images per tile for robust temporal statistics. Each image takes ~102 s to fetch at this size; 12 images ~20 min per tile.

## Scan types (15 defined, 12 enabled)

**Temporal:** temporal_variance_99, temporal_variance_999, temporal_cv, temporal_mad, seasonal_difference, multitemporal_change
**Polarimetric:** crosspol_ratio, crosspol_ratio_variance
**Spatial:** texture_glcm, edge_detection, spatial_autocorrelation
**Baseline:** backscatter_intensity (reference map)
**Disabled:** coherence_coh12, insar_displacement, ml_detector

## Scan regions (from scan.json)

1. **western_desert_egypt** (priority 1) -- buried river channels, Roman-era sites
2. **rub_al_khali** (priority 2) -- Arabian Empty Quarter, Ubar-era trade routes
3. **taklamakan** (priority 3) -- Silk Road sites, buried Buddhist settlements
4. **sahel_mali_niger** (priority 4) -- Garamantian-era settlements, ancient Lake Chad shorelines

## Job coordination

Jobs claim tiles via `claimed_tiles.jsonl` (append-only, TTL 180 min). Completed tiles go in `processed_tiles.jsonl`. Push with retry loop (max 10 retries, pull --rebase + random jitter). Multiple clusters self-coordinate through the same repo.

## Repo layout

| What | Where |
|------|-------|
| Master config | `config/scan.json` |
| Tile list | `config/target_tiles.json` |
| Tiles done | `processed_tiles.jsonl` |
| Tiles claimed | `claimed_tiles.jsonl` |
| Per-tile results | `results/<tile_id>/stack.tif`, `results/<tile_id>/<scan_type>/` |
| Aggregate | `results/all_candidates.geojson` (rebuilt by `rebuild_aggregate.py`) |

## Env vars

REPO_URL, CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, GIT_SSH_COMMAND (all in `~/.bashrc`). Optional: BATCH_SIZE, CLUSTER_ID, SCRATCH_DIR. See `docs/SERVICES_AND_ENV.md`.

## Scaling (at 5 km / 500 px tiles)

| Scale | Tiles | Storage | Time (1 worker) | Time (50 workers) |
|-------|-------|---------|-----------------|-------------------|
| One region (Western Desert) | ~11,000 | ~209 GB | ~5 months | ~3 days |
| Four regions | ~62,000 | ~1.2 TB | ~2.4 years | ~18 days |
| All world deserts | ~480,000 | ~9 TB | -- | ~6 months |

At 5 km tiles the count is higher but each tile is smaller to fetch and store. Commercial CDSE tier allows larger requests (25 km / 2500 px) which cuts tile count by 25x.
