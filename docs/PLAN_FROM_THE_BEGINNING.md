# Plan from the beginning (v3)

## What we do

Scan deserts with Sentinel-1 radar to find candidate locations where structures may be buried. One Git repo (`git@github.com:ualberta-rcg/project-atlantis.git`) holds config, tracking, and results. Jobs clone the repo, claim tiles, fetch imagery once per tile, run all enabled scan types, and push results back. No database.

## Design: fetch once, analyze many

Fetching from the CDSE API is slow (minutes per tile, rate-limited). Running 12 analyses on the same data is cheap (seconds of CPU). So each job:

1. Claims tiles (by tile_id only) from `config/target_tiles.json`.
2. For each tile: fetches 8-15 S1 images (same bbox, 2500x2500 px) once.
3. Builds stack once: mean, var, std, median for VV and VH (8-band `stack.tif`).
4. Runs every enabled scan type from `config/scan.json` on that stack.
5. Appends to `processed_tiles.jsonl` (tile_id, scan_types_run, candidates_by_type, images_used).
6. Pushes with retry (pull --rebase + jitter).

## Resolution

10 m/pixel -- the maximum useful resolution from Sentinel-1 IW GRD. Tiles are 25x25 km = 2500x2500 pixels. Preferred 12 images per tile for robust temporal statistics.

## Scan types (15 defined, 12 enabled)

**Temporal:** temporal_variance_95, temporal_variance_99, temporal_cv, temporal_mad, seasonal_difference, multitemporal_change
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

## Scaling

| Scale | Tiles | Storage | Time (commercial CDSE) |
|-------|-------|---------|----------------------|
| One region (Western Desert) | ~440 | ~48 GB | ~1 day |
| Four regions | ~2,500 | ~275 GB | ~1 week |
| All world deserts | ~50,000 | ~5.5 TB | ~2 months |
