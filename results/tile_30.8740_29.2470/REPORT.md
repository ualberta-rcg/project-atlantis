# Tile Report: tile_30.8740_29.2470

**Bbox:** 30.8740, 29.2470 to 30.9260, 29.2930

**Images:** 11 Sentinel-1 scenes, 10m resolution, 500x500px

**Runtime:** 870s (worker manual-test, 2026-03-17T00:22:00Z)

## Scan Types Run

| Scan Type | Candidates | Status |
|-----------|-----------|--------|
| backscatter_intensity | 0 | ok |
| db_variance | 2500 | ok |
| depolarization_fraction | 12487 | ok |
| hotspot_cluster | 1004 | ok |
| local_contrast | 12500 | ok |
| moisture_differential | 12500 | ok |
| speckle_divergence | 2500 | ok |
| temporal_variance_99 | 2500 | ok |
| temporal_variance_999 | 250 | ok |

**Total scan types:** 9

## Top Candidates Summary

**Total ranked locations:** 1181

| Confidence Tier | Count | Meaning |
|----------------|-------|---------|
| All 16 types agree | 0 | Highest confidence |
| 14-15 types agree | 0 | Very high confidence |
| 10-13 types agree | 0 | High confidence |
| 5-9 types agree | 430 | Moderate confidence |
| 3-4 types agree | 574 | Low confidence (hotspot) |
| 1-2 types (single scan) | 177 | Single-scan only |

## Top 20 Locations

| Rank | Lon | Lat | Confidence | Types Agreeing | Source |
|------|-----|-----|------------|----------------|--------|
| 1 | 30.91626 | 29.28015 | 7 | 7 | hotspot_cluster |
| 2 | 30.91560 | 29.27938 | 7 | 7 | hotspot_cluster |
| 3 | 30.91661 | 29.28568 | 7 | 7 | hotspot_cluster |
| 4 | 30.89625 | 29.25477 | 7 | 7 | hotspot_cluster |
| 5 | 30.91586 | 29.28596 | 7 | 7 | hotspot_cluster |
| 6 | 30.91925 | 29.28128 | 7 | 7 | hotspot_cluster |
| 7 | 30.91538 | 29.28510 | 7 | 7 | hotspot_cluster |
| 8 | 30.91541 | 29.28065 | 7 | 7 | hotspot_cluster |
| 9 | 30.89914 | 29.25033 | 7 | 7 | hotspot_cluster |
| 10 | 30.91975 | 29.25436 | 7 | 7 | hotspot_cluster |
| 11 | 30.90015 | 29.25075 | 7 | 7 | hotspot_cluster |
| 12 | 30.91694 | 29.28656 | 7 | 7 | hotspot_cluster |
| 13 | 30.91953 | 29.25389 | 7 | 7 | hotspot_cluster |
| 14 | 30.87702 | 29.26998 | 7 | 7 | hotspot_cluster |
| 15 | 30.91903 | 29.28181 | 7 | 7 | hotspot_cluster |
| 16 | 30.91987 | 29.28094 | 7 | 7 | hotspot_cluster |
| 17 | 30.89698 | 29.25445 | 7 | 7 | hotspot_cluster |
| 18 | 30.87731 | 29.25084 | 7 | 7 | hotspot_cluster |
| 19 | 30.91937 | 29.28586 | 7 | 7 | hotspot_cluster |
| 20 | 30.89568 | 29.25462 | 7 | 7 | hotspot_cluster |

## Files

- `top_candidates.geojson` — all ranked candidates (open in QGIS or GitHub map)
- `top_candidates.csv` — same data, spreadsheet-friendly
- `hotspot_cluster/` — multi-scan-type agreement analysis
- `*/anomaly.png` — visual heatmap per scan type (viewable on GitHub)

---
*Generated 2026-03-17T01:51:49Z*
