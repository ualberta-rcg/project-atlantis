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

| Component | Size per tile |
|-----------|--------------|
| stack.tif (8 bands, float32) | ~25 MB |
| Per scan type (anomaly.tif + candidates) | ~7 MB each |
| 12 enabled scan types | ~84 MB total |
| Process records + metadata | ~50 KB |
| **Total committed per tile** | **~110 MB** |

Git LFS is required (`.gitattributes` tracks `results/**/*.tif`).
