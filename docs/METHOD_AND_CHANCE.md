# How we find candidates and what "chance" means

## Did we use time displacement?

**Variance pipeline:** We did **not** use InSAR or displacement in the default run. We use **temporal variance** of backscatter only.

**Adding time displacement:** We support two ways to add it (see **docs/INSAR_AND_DISPLACEMENT.md**): (1) **Coherence** (CARD-COH12 on-demand) as a “change between two dates” proxy; (2) **Full InSAR** (SLC download + ISCE2) for displacement in mm when the ground shifts. Both can be combined with the variance-based “chance” so that structures under sand or canopy show up as the earth moves.

- **What we do:** **Temporal variance of backscatter.** We take 2–5 Sentinel-1 images (same area, different dates), compute the **variance** of VV and VH over time at each pixel. Pixels that change a lot over time (high variance) are flagged as candidates. That can reveal subsurface contrast (e.g. buried structure affecting moisture or roughness) or stable features that stand out from the background.
- **Time displacement (InSAR)** would mean: phase difference between two SLC (Single Look Complex) acquisitions → ground movement in mm/year. That’s a different product (needs SLC data and ISCE2 or similar). We could add it later for “ground moving” sites, but the current pipeline does **not** use it.

So we find candidates from **backscatter change over time** (variance), not from displacement.

## What is "chance"?

- **chance** is a number from **0 to 1** (you can show it as 0–100%) for each candidate point.
- It means: **how much more anomalous this pixel is than the cutoff.**  
  - 0 = barely above the variance threshold (we still flag it, but it’s the weakest).  
  - 1 = the highest variance in the scene (strongest anomaly).
- So **higher chance = higher likelihood something is there** in the sense of “stronger backscatter-change signal,” not a calibrated probability. It’s a **relative** score so you can sort or filter (e.g. “show only chance ≥ 0.7”) to focus on the best spots.

It is stored in:

- **candidates.csv** — column `chance`
- **candidates.geojson** — `properties.chance`
