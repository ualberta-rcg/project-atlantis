# Results

Per-tile results from the v3 pipeline. Each tile gets:

- `results/<tile_id>/stack.tif` -- shared base layer (mean/var/std/median VV+VH)
- `results/<tile_id>/<scan_type>/` -- anomaly.tif, candidates.geojson, candidates.csv, metadata.json
- `results/<tile_id>/process_record.json` -- inputs, scan types run, candidate counts

Aggregate: `results/all_candidates.geojson` -- rebuilt by `python scripts/rebuild_aggregate.py`.

Open candidates in QGIS or [geojson.io](https://geojson.io). See `docs/RESULTS_LAYOUT.md` for full layout.
