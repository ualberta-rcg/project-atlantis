# Archaeology Radar Scan (v3)

Scan deserts and high-potential areas with Sentinel-1 radar to find candidate locations where structures or objects may be buried. **Fetch once per tile, run all enabled scan types.** Everything is saved to replicate the process: raw images, stack, analysis outputs, previews, logs.

Everything lives in this Git repo. No database. Jobs clone, claim tiles, process, push.

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
ls results/tile_*/temporal_variance_95/anomaly.png
```

## Tile naming

Tiles are named by coordinates: `tile_<min_lon>_<min_lat>` (e.g. `tile_30.8740_29.2470`). No site names in tile IDs. This ensures unique, sortable, coordinate-based identifiers.

## What gets saved per tile (everything)

```
results/tile_30.8740_29.2470/
├── raw/                            <- all fetched S1 images
│   ├── s1_2019-01-01_to_....tif    <- the actual radar data
│   ├── s1_2019-01-01_to_....png    <- preview (renders on GitHub)
│   └── ...
├── stack.tif                       <- computed stack (mean/var/std/median VV+VH)
├── stack_mean_vv.png               <- preview
├── stack_var_vv.png                <- preview
├── process_record.json             <- full inputs, outputs, timing, reproducibility
├── temporal_variance_95/
│   ├── anomaly.tif + anomaly.png   <- score map + preview
│   ├── candidates.geojson + .csv   <- detected locations
│   └── metadata.json
├── temporal_variance_99/
│   └── ...
├── backscatter_intensity/
│   └── intensity_map.tif + .png
└── combined_top5/                  <- multi-method consensus (highest confidence)
    └── ...
```

**Nothing is excluded.** Raw images, intermediate math, final results, and PNG previews are all committed. Anyone can clone this repo and replicate or extend the analysis without re-fetching from the API.

## Config

- **config/scan.json** -- Master config: scan_regions, tile_defaults (5 km, 10 m, 500x500 px), imagery (8-15 images), scan_types (15 defined, 12 enabled), composite_scores, api_limits.
- **config/target_tiles.json** -- Generated: `python scripts/generate_target_tiles.py --from-scan`
- **config/sites.json** -- Named sites (optional, for reference; tiles still use coord IDs)

## Pipeline (per tile)

1. **Fetch** imagery once (11-12 S1 GRD images, same bbox, 500x500 px at 10 m, ~102 s/image)
2. **Build stack** once (mean/var/std/median VV+VH -> stack.tif)
3. **Run all enabled scan types** (each writes to `results/<tile_id>/<scan_type>/`)
4. **Generate PNG previews** for all TIFFs
5. **Write process record**, append to processed_tiles.jsonl, push

## Scan types (12 enabled by default)

| Category | Scan types |
|----------|-----------|
| Temporal | temporal_variance_95, temporal_variance_99, temporal_cv, temporal_mad, seasonal_difference, multitemporal_change |
| Polarimetric | crosspol_ratio, crosspol_ratio_variance |
| Spatial | texture_glcm, edge_detection, spatial_autocorrelation |
| Baseline | backscatter_intensity (reference map, no candidates) |
| Disabled | coherence_coh12, insar_displacement, ml_detector |

## Self-coordination (no double scanning)

Jobs claim **tiles** via `claimed_tiles.jsonl` (TTL 180 min). Completed tiles tracked in `processed_tiles.jsonl`. Before scanning, each job checks both files and skips any tile already done or claimed. Push with retry (pull --rebase + jitter). Multiple clusters self-coordinate through the repo -- no central scheduler needed.

## Slurm (HPC)

```bash
sbatch --array=0-99 slurm/submit_array.sh
```

Each array task runs `run_pipeline.py`, claims unclaimed tiles, processes, pushes. 100 tasks = 100 independent workers all self-coordinating.

## Env vars

| Variable | Required | Description |
|----------|----------|-------------|
| `REPO_URL` | Yes | `git@github.com:ualberta-rcg/project-atlantis.git` |
| `CDSE_CLIENT_ID` | Yes | CDSE OAuth client ID |
| `CDSE_CLIENT_SECRET` | Yes | CDSE OAuth client secret |
| `GIT_SSH_COMMAND` | Yes | `ssh -i ~/.ssh/archaeology-deploy-key -o StrictHostKeyChecking=accept-new` |
| `BATCH_SIZE` | No | Tiles per claim (default: 5) |
| `CLUSTER_ID` | No | For logging |
