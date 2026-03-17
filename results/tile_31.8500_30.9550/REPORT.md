# Tile Report: tile_31.8500_30.9550

**Bbox:** 31.8500, 30.9550 to 31.9050, 31.0000

**Images:** 12 Sentinel-1 scenes, 10m resolution, 500x500px

**Runtime:** 468.18s (worker slurm-1566, 2026-03-17T01:25:34Z)

## Scan Types Run

| Scan Type | Candidates | Status |
|-----------|-----------|--------|
| backscatter_intensity | 0 | ok |
| crosspol_ratio | 12468 | ok |
| crosspol_ratio_variance | 12500 | ok |
| db_variance | 2500 | ok |
| depolarization_fraction | 12485 | ok |
| edge_detection | 12500 | ok |
| hotspot_cluster | 1619 | ok |
| local_contrast | 12500 | ok |
| moisture_differential | 12500 | ok |
| multitemporal_change | 12500 | ok |
| seasonal_difference | 12500 | ok |
| spatial_autocorrelation | 12500 | ok |
| speckle_divergence | 2500 | ok |
| temporal_cv | 12500 | ok |
| temporal_mad | 12500 | ok |
| temporal_variance_99 | 2500 | ok |
| temporal_variance_999 | 250 | ok |
| texture_glcm | 12500 | ok |

**Total scan types:** 18

## Top Candidates Summary

**Total ranked locations:** 1794

| Confidence Tier | Count | Meaning |
|----------------|-------|---------|
| All 16 types agree | 59 | Highest confidence |
| 14-15 types agree | 129 | Very high confidence |
| 10-13 types agree | 693 | High confidence |
| 5-9 types agree | 661 | Moderate confidence |
| 3-4 types agree | 77 | Low confidence (hotspot) |
| 1-2 types (single scan) | 175 | Single-scan only |

## Top 20 Locations

| Rank | Lon | Lat | Confidence | Types Agreeing | Source |
|------|-----|-----|------------|----------------|--------|
| 1 | 31.87002 | 30.97495 | 16 | 16 | hotspot_cluster |
| 2 | 31.87132 | 30.97569 | 16 | 16 | hotspot_cluster |
| 3 | 31.87507 | 30.99154 | 16 | 16 | hotspot_cluster |
| 4 | 31.86795 | 30.97370 | 16 | 16 | hotspot_cluster |
| 5 | 31.87366 | 30.98330 | 16 | 16 | hotspot_cluster |
| 6 | 31.87693 | 30.97101 | 16 | 16 | hotspot_cluster |
| 7 | 31.87394 | 30.98401 | 16 | 16 | hotspot_cluster |
| 8 | 31.86898 | 30.97485 | 16 | 16 | hotspot_cluster |
| 9 | 31.87070 | 30.97807 | 16 | 16 | hotspot_cluster |
| 10 | 31.87123 | 30.97436 | 16 | 16 | hotspot_cluster |
| 11 | 31.87673 | 30.97045 | 16 | 16 | hotspot_cluster |
| 12 | 31.87018 | 30.97651 | 16 | 16 | hotspot_cluster |
| 13 | 31.87259 | 30.97883 | 16 | 16 | hotspot_cluster |
| 14 | 31.87485 | 30.99187 | 16 | 16 | hotspot_cluster |
| 15 | 31.87118 | 30.97698 | 16 | 16 | hotspot_cluster |
| 16 | 31.87368 | 30.97883 | 16 | 16 | hotspot_cluster |
| 17 | 31.86765 | 30.97471 | 16 | 16 | hotspot_cluster |
| 18 | 31.87415 | 30.98250 | 16 | 16 | hotspot_cluster |
| 19 | 31.86975 | 30.97844 | 16 | 16 | hotspot_cluster |
| 20 | 31.87436 | 30.99145 | 16 | 16 | hotspot_cluster |

## Files

- `top_candidates.geojson` — all ranked candidates (open in QGIS or GitHub map)
- `top_candidates.csv` — same data, spreadsheet-friendly
- `hotspot_cluster/` — multi-scan-type agreement analysis
- `*/anomaly.png` — visual heatmap per scan type (viewable on GitHub)

---
*Generated 2026-03-17T01:51:49Z*
