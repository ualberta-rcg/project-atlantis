# Results layout and findability

## Where to save data

- **Raw imagery (optional):** `data/<site_id>/` — GeoTIFFs from the API (e.g. `s1_2023-01-01_to_2023-01-15.tif`). You can re-fetch by bbox+date, so only keep if you want to avoid re-requesting.
- **Processed stacks:** `data/<site_id>/stack.tif` — temporal mean/variance from 2–5 images (e.g. bands: mean_VV, mean_VH, var_VV, var_VH).
- **Results per site:** `results/<site_id>/`
  - `anomaly.tif` — anomaly/score raster (same grid as stack).
  - `candidates.csv` — one row per candidate: `lon,lat,score,site_id`.
  - `candidates.geojson` — same points as GeoJSON for GIS or web maps.
  - `metadata.json` — bbox, date range, run time, threshold used.
- **Master list of high-confidence spots:** `results/all_candidates.geojson` (and optionally `all_candidates.csv`) — one file that aggregates all sites so “everything with a high chance” is in one place.

Use a stable **site_id** (e.g. `qubbet_el_hawa`, `north_sinai_01`) so paths are predictable.

## Making it easily findable

1. **Consistent structure** — Always write `results/<site_id>/candidates.geojson` and update `results/all_candidates.geojson` when you add a new site. Then “high chance” = open `all_candidates.geojson` in QGIS or a web map.
2. **GitHub** — Push **code** + **results/all_candidates.geojson** (and maybe small `results/*/metadata.json`). Do **not** commit large rasters (add `data/`, `results/*.tif` to `.gitignore`). Optionally commit small thumbnails or a single `results/README.md` that lists sites and links to a map.
3. **Web map (optional)** — Use GitHub Pages + Leaflet: one HTML page that loads `all_candidates.geojson` and shows points with popup (site_id, score). Makes it “click and see” for archaeologists. Repo can host the HTML and the GeoJSON.

## GPU (e.g. 1080 Ti on Slurm)

The current pipeline (stack + variance-based detection) runs on CPU. For a **future ML step** (e.g. CNN on backscatter chips to classify "structure vs no structure"), request a GPU node in the Slurm script (`#SBATCH --gres=gpu:1`) and use the 1080 Ti for inference. Training can also run on the same GPU; 1080 Ti is sufficient for small models and batch sizes.

## Summary

| What | Where | In Git? |
|------|--------|---------|
| Code | `scripts/`, `docs/` | Yes |
| Per-site candidates | `results/<site_id>/candidates.geojson`, `.csv` | Yes (or only aggregated) |
| All high-chance spots | `results/all_candidates.geojson` | Yes |
| Anomaly rasters | `results/<site_id>/anomaly.tif` | No (too large) or use Git LFS |
| Raw/stack imagery | `data/<site_id>/` | No |
