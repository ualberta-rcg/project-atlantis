# Results

Scan results organized by coordinate-based tile ID: `tile_<min_lon>_<min_lat>`.

Each tile directory contains **everything needed to replicate the analysis**:
- `raw/` -- all fetched S1 images (.tif) + PNG previews
- `stack.tif` -- computed temporal stack (mean/var/std/median VV+VH)
- `stack_mean_vv.png`, `stack_var_vv.png` -- stack previews
- `<scan_type>/` -- anomaly.tif, anomaly.png, candidates.geojson, candidates.csv, metadata.json
- `process_record.json` -- full record of inputs, parameters, outputs, timing

Aggregate: `all_candidates.geojson` -- rebuilt by `python scripts/rebuild_aggregate.py`.

PNG files render directly on GitHub for quick visual inspection.

See `docs/RESULTS_LAYOUT.md` for full layout and data sizes.
