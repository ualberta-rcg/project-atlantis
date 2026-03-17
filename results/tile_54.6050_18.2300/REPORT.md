# Tile Report: tile_54.6050_18.2300

**Bbox:** 54.6050, 18.2300 to 54.6600, 18.2800

**Images:** 12 Sentinel-1 scenes, 10m resolution, 500x500px

**Runtime:** 474.49s (worker slurm-1567, 2026-03-17T01:25:41Z)

## Scan Types Run

| Scan Type | Candidates | Status |
|-----------|-----------|--------|
| backscatter_intensity | 0 | ok |
| crosspol_ratio | 12470 | ok |
| crosspol_ratio_variance | 12500 | ok |
| db_variance | 2500 | ok |
| depolarization_fraction | 12486 | ok |
| edge_detection | 12500 | ok |
| hotspot_cluster | 1852 | ok |
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

**Total ranked locations:** 2034

| Confidence Tier | Count | Meaning |
|----------------|-------|---------|
| All 16 types agree | 63 | Highest confidence |
| 14-15 types agree | 551 | Very high confidence |
| 10-13 types agree | 1014 | High confidence |
| 5-9 types agree | 210 | Moderate confidence |
| 3-4 types agree | 14 | Low confidence (hotspot) |
| 1-2 types (single scan) | 182 | Single-scan only |

## Top 20 Locations

| Rank | Lon | Lat | Confidence | Types Agreeing | Source |
|------|-----|-----|------------|----------------|--------|
| 1 | 54.65839 | 18.24227 | 16 | 16 | hotspot_cluster |
| 2 | 54.60709 | 18.27480 | 16 | 16 | hotspot_cluster |
| 3 | 54.60580 | 18.27528 | 16 | 16 | hotspot_cluster |
| 4 | 54.64686 | 18.25177 | 16 | 16 | hotspot_cluster |
| 5 | 54.64570 | 18.26513 | 16 | 16 | hotspot_cluster |
| 6 | 54.65929 | 18.27576 | 16 | 16 | hotspot_cluster |
| 7 | 54.65445 | 18.25876 | 16 | 16 | hotspot_cluster |
| 8 | 54.65111 | 18.24622 | 16 | 16 | hotspot_cluster |
| 9 | 54.64053 | 18.23917 | 16 | 16 | hotspot_cluster |
| 10 | 54.64750 | 18.23595 | 16 | 16 | hotspot_cluster |
| 11 | 54.61871 | 18.25255 | 16 | 16 | hotspot_cluster |
| 12 | 54.65915 | 18.24169 | 16 | 16 | hotspot_cluster |
| 13 | 54.64702 | 18.26508 | 16 | 16 | hotspot_cluster |
| 14 | 54.65838 | 18.27597 | 16 | 16 | hotspot_cluster |
| 15 | 54.65366 | 18.24345 | 16 | 16 | hotspot_cluster |
| 16 | 54.65911 | 18.26044 | 16 | 16 | hotspot_cluster |
| 17 | 54.65453 | 18.24413 | 16 | 16 | hotspot_cluster |
| 18 | 54.65174 | 18.24642 | 16 | 16 | hotspot_cluster |
| 19 | 54.65354 | 18.26361 | 16 | 16 | hotspot_cluster |
| 20 | 54.65707 | 18.25124 | 16 | 16 | hotspot_cluster |

## Files

- `top_candidates.geojson` — all ranked candidates (open in QGIS or GitHub map)
- `top_candidates.csv` — same data, spreadsheet-friendly
- `hotspot_cluster/` — multi-scan-type agreement analysis
- `*/anomaly.png` — visual heatmap per scan type (viewable on GitHub)

---
*Generated 2026-03-17T01:51:49Z*
