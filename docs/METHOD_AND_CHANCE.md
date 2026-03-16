# How we find candidates and what "chance" means

## What we do (v3)

We run **all enabled scan types** from `config/scan.json` on each tile. Each scan type detects different kinds of anomalies:

- **Temporal** (variance_95/99, cv, mad, seasonal_difference, multitemporal_change) -- how pixel brightness varies over 8-15 images across time.
- **Polarimetric** (crosspol_ratio, crosspol_ratio_variance) -- how the VH/VV scattering ratio differs from surroundings or fluctuates.
- **Spatial** (texture_glcm, edge_detection, spatial_autocorrelation) -- patterns in the mean backscatter image (texture, edges, clustering).
- **Baseline** (backscatter_intensity) -- reference map, no candidates.
- **Composite** (combined_top5) -- weighted combination of top 5 scan types; candidates must appear in at least 2 methods.

The composite score (`combined_top5`) gives highest confidence: a candidate flagged by variance, texture, AND edge detection is almost certainly real. A candidate flagged by only one method could be noise.

## What is "chance"?

- **chance** is a number from **0 to 1** (0-100%) for each candidate point.
- It means: **how much more anomalous this pixel is than the threshold.**
  - 0 = barely above the threshold (weakest candidate).
  - 1 = the strongest anomaly in the tile.
- Formula (most scan types): `chance = (score - threshold) / (max_score - threshold)`, clamped 0-1.
- **Higher chance = stronger anomaly signal**, not a calibrated probability. Use it to sort/filter (e.g. "show only chance >= 0.7").

Stored in:
- **candidates.csv** -- column `chance`
- **candidates.geojson** -- `properties.chance`

## InSAR and coherence

**Disabled by default.** Two optional scan types add displacement/coherence:

- **coherence_coh12** -- downloads pre-computed 12-day coherence from CDSE. High variance + high coherence = likely subsurface feature. High variance + low coherence = likely surface noise. Enable in scan.json for high-priority regions.
- **insar_displacement** -- full InSAR from SLC data via ISCE2. Measures actual ground displacement in mm. Enable for tiles with high-confidence candidates. See `docs/INSAR_AND_DISPLACEMENT.md`.
