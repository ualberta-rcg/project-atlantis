# Results layout (v3)

## Per tile

Each processed tile writes to `results/<tile_id>/`:

```
results/<tile_id>/
├── stack.tif                    <- shared base: mean/var/std/median VV+VH (8 bands)
├── process_record.json          <- covers all scan types for this tile
├── temporal_variance_95/
│   ├── anomaly.tif              <- score raster
│   ├── candidates.geojson       <- detected locations with score + chance
│   ├── candidates.csv           <- same data, tabular
│   └── metadata.json            <- runtime, threshold, candidate count
├── temporal_variance_99/
│   └── ...
├── temporal_cv/
├── temporal_mad/
├── seasonal_difference/
├── crosspol_ratio/
├── crosspol_ratio_variance/
├── texture_glcm/
├── edge_detection/
│   ├── anomaly.tif
│   ├── edges.tif                <- binary edge map
│   ├── linear_features.geojson  <- detected line segments
│   ├── candidates.geojson
│   └── metadata.json
├── spatial_autocorrelation/
├── multitemporal_change/
├── backscatter_intensity/
│   └── intensity_map.tif        <- reference layer, no candidates
└── combined_top5/
    ├── anomaly.tif
    ├── candidates.geojson       <- highest confidence: multi-method agreement
    ├── candidates.csv
    └── metadata.json
```

## Aggregate

- `results/all_candidates.geojson` -- rebuilt by `python scripts/rebuild_aggregate.py`. Aggregates candidates from all tiles and scan types. Each feature has `tile_id` and `scan_type`. Open in QGIS or [geojson.io](https://geojson.io).

## What goes in Git

| What | Where | In Git? |
|------|-------|---------|
| Code | `scripts/`, `docs/` | Yes |
| Config | `config/scan.json`, `config/target_tiles.json` | Yes |
| Per-tile results (all scan types) | `results/<tile_id>/` | Yes (Git LFS for *.tif) |
| All candidates | `results/all_candidates.geojson` | Yes |
| Tracking | `processed_tiles.jsonl`, `claimed_tiles.jsonl` | Yes |
| Raw fetched images | scratch disk | No (not committed) |

## Data sizes

| Component | Size per tile (5 km / 500 px) |
|-----------|-------------------------------|
| One raw image (VV + VH + mask, float32) | ~1.85 MB |
| 12 raw images (scratch, not committed) | ~22 MB |
| stack.tif (8 bands, float32) | ~4 MB |
| Per scan type (anomaly.tif + candidates) | ~1.2 MB each |
| 12 enabled scan types | ~15 MB total |
| Process records + metadata | ~50 KB |
| **Total committed per tile** | **~19 MB** |

## Measured API timing (free tier, CDSE Process API)

| Tile size | Pixels | Resolution | Time per image | File size |
|-----------|--------|-----------|---------------|-----------|
| **5 km / 500 px** | 500x500 | **10 m** | **~102 s** | **1.85 MB** |
| 5 km / 250 px | 250x250 | 20 m | ~11 s | 0.47 MB |
| 25 km / 500 px | 500x500 | 50 m | ~11 s | 1.93 MB |
| 25 km / 1000 px | 1000x1000 | 25 m | ~23 s | 7.71 MB |
| 25 km / 2500 px | 2500x2500 | 10 m | >5 min (timeout) | -- |

The 5 km / 500 px tile at 10 m resolution is the practical sweet spot on the free tier: full native resolution, reasonable fetch time (~20 min for 12 images).

Git LFS is required (`.gitattributes` tracks `results/**/*.tif`).
