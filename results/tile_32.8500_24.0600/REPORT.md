# Tile Report: tile_32.8500_24.0600

**Bbox:** 32.8500, 24.0600 to 32.9300, 24.1400

**Images:** 12 Sentinel-1 scenes, 10m resolution, 500x500px

**Runtime:** 987.78s (worker slurm-1569, 2026-03-17T02:09:47Z)

## Scan Types Run

| Scan Type | Candidates | Status |
|-----------|-----------|--------|
| backscatter_intensity | 0 | ok |
| crosspol_ratio | 12471 | ok |
| crosspol_ratio_variance | 12500 | ok |
| db_variance | 2500 | ok |
| depolarization_fraction | 12487 | ok |
| edge_detection | 12500 | ok |
| hotspot_cluster | 3775 | ok |
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

**Total ranked locations:** 3949

| Confidence Tier | Count | Meaning |
|----------------|-------|---------|
| All 16 types agree | 28 | Highest confidence |
| 14-15 types agree | 201 | Very high confidence |
| 10-13 types agree | 843 | High confidence |
| 5-9 types agree | 2171 | Moderate confidence |
| 3-4 types agree | 532 | Low confidence (hotspot) |
| 1-2 types (single scan) | 174 | Single-scan only |

## Top 20 Locations

| Rank | Lon | Lat | Confidence | Types Agreeing | Source |
|------|-----|-----|------------|----------------|--------|
| 1 | 32.90788 | 24.08658 | 16 | 16 | hotspot_cluster |
| 2 | 32.89775 | 24.09770 | 16 | 16 | hotspot_cluster |
| 3 | 32.89962 | 24.10437 | 16 | 16 | hotspot_cluster |
| 4 | 32.90649 | 24.10808 | 16 | 16 | hotspot_cluster |
| 5 | 32.90747 | 24.08698 | 16 | 16 | hotspot_cluster |
| 6 | 32.87567 | 24.06524 | 16 | 16 | hotspot_cluster |
| 7 | 32.89953 | 24.10696 | 16 | 16 | hotspot_cluster |
| 8 | 32.89694 | 24.09667 | 16 | 16 | hotspot_cluster |
| 9 | 32.91196 | 24.06150 | 16 | 16 | hotspot_cluster |
| 10 | 32.87629 | 24.06588 | 16 | 16 | hotspot_cluster |
| 11 | 32.89877 | 24.10553 | 16 | 16 | hotspot_cluster |
| 12 | 32.89958 | 24.10824 | 16 | 16 | hotspot_cluster |
| 13 | 32.89780 | 24.09888 | 16 | 16 | hotspot_cluster |
| 14 | 32.91817 | 24.06818 | 16 | 16 | hotspot_cluster |
| 15 | 32.89899 | 24.10163 | 16 | 16 | hotspot_cluster |
| 16 | 32.90839 | 24.08749 | 16 | 16 | hotspot_cluster |
| 17 | 32.89367 | 24.12496 | 16 | 16 | hotspot_cluster |
| 18 | 32.91790 | 24.06702 | 16 | 16 | hotspot_cluster |
| 19 | 32.89844 | 24.10214 | 16 | 16 | hotspot_cluster |
| 20 | 32.89435 | 24.12576 | 16 | 16 | hotspot_cluster |

## Files

- `top_candidates.geojson` — all ranked candidates (open in QGIS or GitHub map)
- `top_candidates.csv` — same data, spreadsheet-friendly
- `hotspot_cluster/` — multi-scan-type agreement analysis
- `*/anomaly.png` — visual heatmap per scan type (viewable on GitHub)

---
*Generated 2026-03-17T02:09:49Z*
