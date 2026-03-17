#!/usr/bin/env python3
"""
Generate a final report for a processed tile: ranked GeoJSON, CSV, and markdown
summary of the highest-confidence candidates from all scan types.

The report combines:
  1. Hotspot clusters (locations where multiple scan types agree)
  2. Top candidates from speckle_divergence and temporal_variance_999
  3. A human-readable markdown summary

Outputs (in <tile_dir>/):
  - REPORT.md              — human-readable summary with top locations
  - top_candidates.geojson — ranked GeoJSON of best candidates (viewable on GitHub map)
  - top_candidates.csv     — same data, tabular

Usage:
  python tile_report.py results/tile_31.8500_30.9550
  python tile_report.py results/tile_31.8500_30.9550 results/tile_54.6050_18.2300
"""
import os
import sys
import json
import glob
from datetime import datetime


def load_geojson(path):
    if not os.path.isfile(path):
        return []
    with open(path) as f:
        fc = json.load(f)
    return fc.get("features", [])


def load_metadata(path):
    if not os.path.isfile(path):
        return {}
    with open(path) as f:
        return json.load(f)


def generate_report(tile_dir):
    tile_id = os.path.basename(tile_dir)
    process_record = load_metadata(os.path.join(tile_dir, "process_record.json"))

    # Collect all scan type results
    scan_results = {}
    for meta_path in sorted(glob.glob(os.path.join(tile_dir, "*", "metadata.json"))):
        scan_name = os.path.basename(os.path.dirname(meta_path))
        meta = load_metadata(meta_path)
        n = meta.get("num_candidates", meta.get("candidate_count", 0))
        scan_results[scan_name] = {
            "candidates": n,
            "threshold": meta.get("threshold_used"),
            "percentile": meta.get("percentile_threshold"),
            "status": meta.get("status", "ok"),
        }

    # Build ranked candidate list from hotspot_cluster (best source)
    hotspot_features = load_geojson(os.path.join(tile_dir, "hotspot_cluster", "candidates.geojson"))

    # Also pull top candidates from high-confidence scan types as fallback
    high_conf_types = ["speckle_divergence", "temporal_variance_999", "db_variance"]
    high_conf_candidates = []
    for st in high_conf_types:
        feats = load_geojson(os.path.join(tile_dir, st, "candidates.geojson"))
        for f in feats:
            f["properties"]["source_scan"] = st
        high_conf_candidates.extend(feats)

    # Rank hotspots by agreeing_types descending, then by n_candidates
    hotspot_features.sort(
        key=lambda f: (-f["properties"].get("agreeing_types", 0),
                       -f["properties"].get("n_candidates", 0)))

    # Build top_candidates: hotspots first (deduplicated), then high-conf scan type picks
    top_features = []
    seen_coords = set()

    for feat in hotspot_features:
        lon = round(feat["geometry"]["coordinates"][0], 5)
        lat = round(feat["geometry"]["coordinates"][1], 5)
        key = (lon, lat)
        if key in seen_coords:
            continue
        seen_coords.add(key)
        props = feat["properties"]
        top_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "rank": len(top_features) + 1,
                "lon": lon, "lat": lat,
                "confidence": props.get("agreeing_types", 0),
                "agreeing_types": props.get("agreeing_types", 0),
                "types": props.get("types", []),
                "n_candidates_in_cluster": props.get("n_candidates", 0),
                "source": "hotspot_cluster",
                "tile_id": tile_id,
            },
        })

    # Add high-confidence scan-type candidates not already covered
    for feat in sorted(high_conf_candidates, key=lambda f: -f["properties"].get("score", 0))[:200]:
        lon = round(feat["geometry"]["coordinates"][0], 5)
        lat = round(feat["geometry"]["coordinates"][1], 5)
        key = (lon, lat)
        if key in seen_coords:
            continue
        seen_coords.add(key)
        props = feat["properties"]
        top_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "rank": len(top_features) + 1,
                "lon": lon, "lat": lat,
                "confidence": 1,
                "agreeing_types": 1,
                "types": [props.get("source_scan", props.get("pathway", "unknown"))],
                "score": props.get("score"),
                "chance": props.get("chance"),
                "source": props.get("source_scan", "single_scan"),
                "tile_id": tile_id,
            },
        })

    # Write top_candidates.geojson
    geojson_out = os.path.join(tile_dir, "top_candidates.geojson")
    with open(geojson_out, "w") as f:
        json.dump({"type": "FeatureCollection", "features": top_features}, f, indent=2)

    # Write top_candidates.csv
    csv_out = os.path.join(tile_dir, "top_candidates.csv")
    with open(csv_out, "w") as f:
        f.write("rank,lon,lat,confidence,agreeing_types,source,types,tile_id\n")
        for feat in top_features:
            p = feat["properties"]
            types_str = ";".join(p.get("types", []))
            f.write(f'{p["rank"]},{p["lon"]},{p["lat"]},{p["confidence"]},'
                    f'{p["agreeing_types"]},{p["source"]},"{types_str}",{tile_id}\n')

    # Inputs info
    inputs = process_record.get("inputs", {})
    bbox = inputs.get("bbox", [])
    run_meta = process_record.get("run_metadata", {})

    # Count by confidence tier
    tiers = {"16": 0, "14-15": 0, "10-13": 0, "5-9": 0, "3-4": 0, "1-2": 0}
    for feat in top_features:
        a = feat["properties"]["agreeing_types"]
        if a >= 16:
            tiers["16"] += 1
        elif a >= 14:
            tiers["14-15"] += 1
        elif a >= 10:
            tiers["10-13"] += 1
        elif a >= 5:
            tiers["5-9"] += 1
        elif a >= 3:
            tiers["3-4"] += 1
        else:
            tiers["1-2"] += 1

    # Write REPORT.md
    md_out = os.path.join(tile_dir, "REPORT.md")
    with open(md_out, "w") as f:
        f.write(f"# Tile Report: {tile_id}\n\n")
        if bbox:
            f.write(f"**Bbox:** {bbox[0]:.4f}, {bbox[1]:.4f} to {bbox[2]:.4f}, {bbox[3]:.4f}\n\n")
        f.write(f"**Images:** {inputs.get('image_count', '?')} Sentinel-1 scenes, "
                f"{inputs.get('resolution_m', 10)}m resolution, "
                f"{inputs.get('size_px', ['?','?'])[0]}x{inputs.get('size_px', ['?','?'])[1]}px\n\n")
        f.write(f"**Runtime:** {run_meta.get('runtime_seconds', '?')}s "
                f"(worker {run_meta.get('worker_id', '?')}, "
                f"{run_meta.get('timestamp_iso', '?')})\n\n")

        f.write("## Scan Types Run\n\n")
        f.write("| Scan Type | Candidates | Status |\n")
        f.write("|-----------|-----------|--------|\n")
        for name, info in sorted(scan_results.items()):
            f.write(f"| {name} | {info['candidates']} | {info['status']} |\n")
        f.write(f"\n**Total scan types:** {len(scan_results)}\n\n")

        f.write("## Top Candidates Summary\n\n")
        f.write(f"**Total ranked locations:** {len(top_features)}\n\n")
        f.write("| Confidence Tier | Count | Meaning |\n")
        f.write("|----------------|-------|---------|\n")
        f.write(f"| All 16 types agree | {tiers['16']} | Highest confidence |\n")
        f.write(f"| 14-15 types agree | {tiers['14-15']} | Very high confidence |\n")
        f.write(f"| 10-13 types agree | {tiers['10-13']} | High confidence |\n")
        f.write(f"| 5-9 types agree | {tiers['5-9']} | Moderate confidence |\n")
        f.write(f"| 3-4 types agree | {tiers['3-4']} | Low confidence (hotspot) |\n")
        f.write(f"| 1-2 types (single scan) | {tiers['1-2']} | Single-scan only |\n")

        f.write("\n## Top 20 Locations\n\n")
        f.write("| Rank | Lon | Lat | Confidence | Types Agreeing | Source |\n")
        f.write("|------|-----|-----|------------|----------------|--------|\n")
        for feat in top_features[:20]:
            p = feat["properties"]
            f.write(f"| {p['rank']} | {p['lon']:.5f} | {p['lat']:.5f} | "
                    f"{p['confidence']} | {p['agreeing_types']} | {p['source']} |\n")

        f.write("\n## Files\n\n")
        f.write("- `top_candidates.geojson` — all ranked candidates (open in QGIS or GitHub map)\n")
        f.write("- `top_candidates.csv` — same data, spreadsheet-friendly\n")
        f.write("- `hotspot_cluster/` — multi-scan-type agreement analysis\n")
        f.write("- `*/anomaly.png` — visual heatmap per scan type (viewable on GitHub)\n")
        f.write(f"\n---\n*Generated {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}*\n")

    print(f"[report] {tile_id}: {len(top_features)} ranked candidates, "
          f"{tiers['16']} at max confidence")
    print(f"  -> {md_out}")
    print(f"  -> {geojson_out}")
    print(f"  -> {csv_out}")
    return len(top_features)


def main():
    if len(sys.argv) < 2:
        print("Usage: tile_report.py <tile_dir> [tile_dir2 ...]", file=sys.stderr)
        sys.exit(1)
    for d in sys.argv[1:]:
        if not os.path.isdir(d):
            print(f"Skip (not a dir): {d}", file=sys.stderr)
            continue
        generate_report(d)


if __name__ == "__main__":
    main()
