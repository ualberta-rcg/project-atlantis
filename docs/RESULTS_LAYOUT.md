# Results layout (v3)

## Tile naming

Tiles are named by their southwest corner coordinates: `tile_<min_lon>_<min_lat>` (e.g. `tile_30.8740_29.2470`). This ensures unique, coordinate-based IDs that don't depend on site names.

## Per tile -- everything is saved

Each tile saves **all data needed to replicate the process**: raw fetched images, computed stack, every scan type's outputs, previews, and the process record.

```
results/tile_30.8740_29.2470/
├── raw/                                <- fetched S1 images (the input data)
│   ├── s1_2019-01-01_to_2019-01-15.tif
│   ├── s1_2019-01-01_to_2019-01-15.png <- preview (VV/VH composite, renders on GitHub)
│   ├── s1_2019-09-01_to_2019-09-15.tif
│   ├── s1_2019-09-01_to_2019-09-15.png
│   └── ... (one .tif + .png per date)
├── stack.tif                           <- 8-band stack (mean/var/std/median VV+VH)
├── stack_mean_vv.png                   <- preview of mean VV band
├── stack_var_vv.png                    <- preview of variance VV band
├── process_record.json                 <- full record: inputs, scan types, candidates, timing
├── temporal_variance_99/
│   ├── anomaly.tif                     <- score raster (top 1%)
│   ├── anomaly.png                     <- preview (renders on GitHub)
│   ├── candidates.geojson              <- detected locations with score + chance
│   ├── candidates.csv                  <- same data, tabular
│   └── metadata.json                   <- runtime, threshold, candidate count
├── temporal_variance_999/
│   └── ... (same structure, top 0.1%)
├── backscatter_intensity/
│   ├── intensity_map.tif               <- reference layer
│   ├── intensity_map.png               <- preview
│   └── metadata.json
└── combined_top5/                      <- (when composite is run)
    └── ...
```

## What gets committed (everything)

| What | Where | In Git? |
|------|-------|---------|
| Raw fetched images | `results/<tile_id>/raw/*.tif` | Yes (Git LFS) |
| PNG previews | `results/<tile_id>/raw/*.png`, `*/anomaly.png`, etc. | Yes (renders on GitHub) |
| Computed stack | `results/<tile_id>/stack.tif` | Yes (Git LFS) |
| Scan type outputs | `results/<tile_id>/<scan_type>/` | Yes |
| Process record | `results/<tile_id>/process_record.json` | Yes |
| Tracking | `processed_tiles.jsonl`, `claimed_tiles.jsonl` | Yes |
| Aggregate | `results/all_candidates.geojson` | Yes |

**Nothing is excluded.** All data needed to replicate the process is in the repo.

## PNG previews

Every `.tif` has a corresponding `.png` that renders directly on GitHub:
- **Raw images:** VV/VH/ratio RGB composite (R=VV, G=VH, B=VV-VH in dB)
- **Stack:** grayscale of mean_VV and var_VV bands
- **Anomaly maps:** grayscale, 2nd-98th percentile stretch
- **Intensity map:** grayscale mean backscatter

## Data sizes (5 km / 500 px tiles)

| Component | Size per tile |
|-----------|--------------|
| 11 raw images (.tif) | ~21 MB |
| 11 raw previews (.png) | ~6 MB |
| stack.tif (8 bands) | ~7 MB |
| Stack previews (.png) | ~0.4 MB |
| Per scan type (anomaly.tif + candidates + preview) | ~7 MB each |
| Process records + metadata | ~50 KB |
| **Total committed per tile** | **~50 MB** |

## Measured API timing (free tier, CDSE Process API)

| Tile size | Pixels | Resolution | Time per image | File size |
|-----------|--------|-----------|---------------|-----------|
| **5 km / 500 px** | 500x500 | **10 m** | **~102 s** | **1.85 MB** |
| 5 km / 250 px | 250x250 | 20 m | ~11 s | 0.47 MB |
| 25 km / 500 px | 500x500 | 50 m | ~11 s | 1.93 MB |
| 25 km / 1000 px | 1000x1000 | 25 m | ~23 s | 7.71 MB |
| 25 km / 2500 px | 2500x2500 | 10 m | >5 min (timeout) | -- |
