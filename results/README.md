# Archaeology detection results

- **Per tile, per pathway:** `results/<tile_id>/<pathway>/` contains:
  - `stack.tif`, `anomaly.tif`, `candidates.csv`, `candidates.geojson`, `metadata.json`, `process_record.json` (and optional `process_record.md`).
  - Optional: `coherence.tif`, `displacement_los.tif` when that pathway includes InSAR.
- **All high-chance spots:** `results/all_candidates.geojson` — aggregates all pathways; each feature has `tile_id` and `pathway`. Open in QGIS or [geojson.io](https://geojson.io).

Full layout and file contents: see plan **sections 5 and 5b**.
