# InSAR and displacement (v3)

Both InSAR scan types are **disabled by default** in `config/scan.json`. Enable them for high-priority tiles that already have strong candidates from other scan types.

## coherence_coh12 (Path A)

- **What:** Downloads pre-computed CARD-COH12 (12-day coherence) from CDSE On-Demand Processing.
- **Measures:** How stable the radar phase is between two dates (0-1). Low coherence = surface changed.
- **Use in pipeline:** Combine with variance: high variance + high coherence = likely subsurface feature (stable surface but anomalous backscatter). High variance + low coherence = surface noise (wind, sand movement) -- likely false positive.
- **API:** Submits order via CDSE ODP, polls until done, downloads result. See `scripts/order_coh12.py`.
- **Enable:** Set `"enabled": true` for `coherence_coh12` in scan.json.

## insar_displacement (Path B)

- **What:** Full InSAR displacement from SLC (Single Look Complex) data via ISCE2.
- **Measures:** Actual line-of-sight surface displacement at mm scale.
- **Detects:** Subsidence over underground voids (tombs, tunnels, collapsed chambers). Differential compaction between buried structures and surrounding fill.
- **Steps:**
  1. Download SLC products from CDSE Catalogue (large files, to scratch disk)
  2. Run ISCE2 topsStack: coregistration, interferogram, phase unwrapping, geocoding
  3. Output: displacement raster + coherence, geocoded to same grid as stack.tif
- **Requirements:** ISCE2 installed (e.g. `module load isce2/2.6.3` on cluster), significant CPU time (~30 min/tile).
- **Enable:** Set `"enabled": true` for `insar_displacement` in scan.json.

## SLC data

- Source: CDSE Catalogue OData API (same token as Process API)
- Filter: `SENTINEL-1`, productType `IW_SLC__1S`, footprint intersects tile bbox
- Resolution: ~2.3 m range x ~14 m azimuth (finer than GRD)
- Coverage: worldwide from Feb 2021; Europe from Oct 2014

## Two-tier strategy

Use the 12 enabled GRD-based scan types as the wide-area screener. When candidates are identified with high confidence (combined_top5), enable InSAR for just those tiles. This avoids the heavy SLC processing for the vast majority of tiles that have no candidates.
