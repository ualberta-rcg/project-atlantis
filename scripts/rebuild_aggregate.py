#!/usr/bin/env python3
"""
Rebuild results/all_candidates.geojson and all_candidates.csv from all
results/<tile_id>/<pathway>/candidates.geojson files. Run this after workers
push (e.g. cron, CI, or manually). Avoids merge conflicts from workers
updating one big file.
"""
import os
import json
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    # v3: results/<tile_id>/<scan_type>/candidates.geojson; also support results/<tile_id>/<pathway>/
    pattern = os.path.join(RESULTS_DIR, "*", "*", "candidates.geojson")
    paths = sorted(glob.glob(pattern))
    features = []
    rows_csv = []
    for path in paths:
        try:
            with open(path) as f:
                fc = json.load(f)
        except Exception as e:
            print(f"Skip {path}: {e}", file=__import__("sys").stderr)
            continue
        for feat in fc.get("features", []):
            props = feat.get("properties", {})
            props.setdefault("pathway", os.path.basename(os.path.dirname(path)))
            props.setdefault("tile_id", os.path.basename(os.path.dirname(os.path.dirname(path))))
            features.append(feat)
            coords = feat.get("geometry", {}).get("coordinates", [0, 0])
            lon, lat = coords[0], coords[1]
            rows_csv.append({
                "lon": lon, "lat": lat,
                "score": props.get("score"), "chance": props.get("chance"),
                "tile_id": props.get("tile_id"), "pathway": props.get("pathway"),
            })

    out_geojson = os.path.join(RESULTS_DIR, "all_candidates.geojson")
    out_csv = os.path.join(RESULTS_DIR, "all_candidates.csv")
    fc_out = {"type": "FeatureCollection", "features": features}
    with open(out_geojson, "w") as f:
        json.dump(fc_out, f, indent=2)
    print(f"Wrote {out_geojson} ({len(features)} features)")

    with open(out_csv, "w") as f:
        f.write("lon,lat,score,chance,tile_id,pathway\n")
        for r in rows_csv:
            f.write(f"{r['lon']},{r['lat']},{r.get('score','')},{r.get('chance','')},{r.get('tile_id','')},{r.get('pathway','')}\n")
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
