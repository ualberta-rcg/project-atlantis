# Time displacement (InSAR) for structures under sand or canopy

## Why we want it

- **Structures under sand or under canopy** can stay invisible in a single image.
- **When the ground shifts over time** (subsidence, seasonal movement, differential settling over buried walls), InSAR measures that **displacement** (mm-scale).
- So **time displacement** lets us see objects when the earth moves: buried features or structures under vegetation can show up as differential motion or loss of coherence between two dates.

We combine two signals:
1. **Backscatter variance** (already in the pipeline) — same spot, different dates; intensity change.
2. **Time displacement / coherence** — phase change (InSAR) or coherence (stability of the phase). Low coherence or nonzero displacement can indicate “something changed here” (e.g. structure under sand or canopy).

## Two ways to get it

### Path A: Coherence (CARD-COH12) — on-demand, no SLC download

- **What:** CDSE **On-Demand Processing** workflow **CARD-COH12**: coherence of a **pair of Sentinel-1 SLC images 12 days apart**. Coherence = how stable the phase is (0–1). **Low coherence** = surface changed (displacement, moisture, vegetation, or scattering change).
- **Pros:** No need to download SLC; you submit an order with one SLC product ID, the service produces a coherence product; you download the result.
- **Cons:** Not true displacement in mm; it’s a proxy for “change between two dates.” Quotas: limited concurrent orders (see CDSE quotas).
- **Use:** Order coherence for a site → get a GeoTIFF (or similar) → use **(1 − coherence)** or low-coherence areas as an extra “chance” layer (e.g. “change here”) and combine with variance-based chance.

### Path B: Full InSAR displacement (SLC + ISCE2)

- **What:** Download **two (or more) Sentinel-1 SLC** products for the same area and two dates → run **ISCE2** on the cluster (coregister, interferogram, unwrap, geocode) → get **displacement in mm** (line-of-sight) and/or coherence.
- **Pros:** Real displacement (mm/year or mm between dates); best for “earth shifted here.”
- **Cons:** Need to discover and download SLC (large files) to `$SCRATCH`; run ISCE2 (topsStack or similar); more setup.
- **Use:** Displacement magnitude or gradient as “chance” layer; combine with variance and optionally coherence.

## Data and tools

- **SLC:** Sentinel-1 IW SLC. Available from CDSE (catalogue OData + download). Rest of World: from Feb 2021; Europe: from Oct 2014.
- **Cluster:** `isce2/2.6.3` on CVMFS for InSAR (Path B). Path A uses CDSE ODP API only.
- **Auth:** Path A uses CDSE (ODP token; may need username/password for On-Demand). Path B uses catalogue + download (same CDSE token as for catalogue).

## Summary

| Goal                         | Path A (coherence)     | Path B (full InSAR)   |
|-----------------------------|------------------------|------------------------|
| “Change between two dates”  | Yes (low coherence)    | Yes (phase + coherence) |
| Displacement in mm          | No                     | Yes                    |
| Use “earth shifts” for find | As proxy (change)      | Direct (displacement)  |
| SLC download                | No                     | Yes                    |
| Cluster (ISCE2)             | No                     | Yes                    |

We add **Path A** first (order CARD-COH12, ingest coherence into the pipeline), then **Path B** (SLC + ISCE2) for full displacement when you need mm-level motion.
