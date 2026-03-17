#!/usr/bin/env python3
"""
Generate a final report for a processed tile.

Clusters nearby hotspot candidates into discrete "sites" (within ~100m),
then ranks them by how many independent scan types agree. Output is capped
at MAX_SITES (default 50) — only the very best locations.

Outputs (in <tile_dir>/):
  - REPORT.md              — human-readable summary
  - top_candidates.geojson — ranked GeoJSON (viewable on GitHub map)
  - top_candidates.csv     — same data, tabular

Usage:
  python tile_report.py results/tile_31.8500_30.9550
"""
import os
import sys
import json
import glob
import math
from datetime import datetime

MAX_SITES = 50
CLUSTER_RADIUS_DEG = 0.001  # ~100m at equator


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


def cluster_points(points, radius_deg):
    """
    Simple greedy clustering: merge points within radius_deg into one site.
    Each point is (lon, lat, agreeing_types, types_list, n_candidates).
    Returns list of site dicts sorted by agreeing_types descending.
    """
    used = [False] * len(points)
    sites = []
    for i, p in enumerate(points):
        if used[i]:
            continue
        used[i] = True
        cluster = [p]
        for j in range(i + 1, len(points)):
            if used[j]:
                continue
            dlat = p[1] - points[j][1]
            dlon = (p[0] - points[j][0]) * math.cos(math.radians(p[1]))
            if math.sqrt(dlat**2 + dlon**2) <= radius_deg:
                used[j] = True
                cluster.append(points[j])
        # Site center = centroid, confidence = max agreeing_types in cluster
        avg_lon = sum(c[0] for c in cluster) / len(cluster)
        avg_lat = sum(c[1] for c in cluster) / len(cluster)
        best = max(cluster, key=lambda c: c[2])
        all_types = set()
        for c in cluster:
            all_types.update(c[3])
        sites.append({
            "lon": round(avg_lon, 5),
            "lat": round(avg_lat, 5),
            "agreeing_types": best[2],
            "types": sorted(all_types),
            "pixel_count": sum(c[4] for c in cluster),
            "cluster_size": len(cluster),
        })
    sites.sort(key=lambda s: (-s["agreeing_types"], -s["pixel_count"]))
    return sites


def generate_report(tile_dir):
    tile_id = os.path.basename(tile_dir)
    process_record = load_metadata(os.path.join(tile_dir, "process_record.json"))

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

    # Load hotspot_cluster candidates (these already have multi-type agreement)
    hotspot_features = load_geojson(
        os.path.join(tile_dir, "hotspot_cluster", "candidates.geojson"))

    # Build point list: (lon, lat, agreeing_types, types, n_candidates)
    raw_points = []
    for feat in hotspot_features:
        coords = feat["geometry"]["coordinates"]
        props = feat["properties"]
        raw_points.append((
            coords[0], coords[1],
            props.get("agreeing_types", 3),
            props.get("types", []),
            props.get("n_candidates", 1),
        ))

    # Cluster into sites
    if raw_points:
        sites = cluster_points(raw_points, CLUSTER_RADIUS_DEG)
    else:
        sites = []

    # Cap at MAX_SITES
    sites = sites[:MAX_SITES]

    # Build GeoJSON features
    top_features = []
    for i, site in enumerate(sites):
        top_features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [site["lon"], site["lat"]]},
            "properties": {
                "rank": i + 1,
                "lon": site["lon"],
                "lat": site["lat"],
                "agreeing_types": site["agreeing_types"],
                "types": site["types"],
                "pixel_count": site["pixel_count"],
                "cluster_size": site["cluster_size"],
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
        f.write("rank,lon,lat,agreeing_types,pixel_count,cluster_size,types,tile_id\n")
        for feat in top_features:
            p = feat["properties"]
            types_str = ";".join(p.get("types", []))
            f.write(f'{p["rank"]},{p["lon"]},{p["lat"]},{p["agreeing_types"]},'
                    f'{p["pixel_count"]},{p["cluster_size"]},"{types_str}",{tile_id}\n')

    # Report metadata
    inputs = process_record.get("inputs", {})
    bbox = inputs.get("bbox", [])
    run_meta = process_record.get("run_metadata", {})
    n_types = len(scan_results)

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
        f.write(f"\n**Total scan types:** {n_types}\n\n")

        f.write(f"## Top Sites (max {MAX_SITES})\n\n")
        f.write(f"**Sites found:** {len(sites)}\n")
        f.write(f"(Nearby pixels clustered within ~100m into single sites)\n\n")

        if sites:
            best = sites[0]["agreeing_types"]
            f.write(f"**Best agreement:** {best}/{n_types} scan types\n\n")
            f.write("| Rank | Lon | Lat | Types Agreeing | Pixels | Google Maps |\n")
            f.write("|------|-----|-----|----------------|--------|-------------|\n")
            for i, site in enumerate(sites):
                gmap = f"https://www.google.com/maps?q={site['lat']},{site['lon']}"
                f.write(f"| {i+1} | {site['lon']:.5f} | {site['lat']:.5f} | "
                        f"{site['agreeing_types']}/{n_types} | {site['pixel_count']} | "
                        f"[map]({gmap}) |\n")
        else:
            f.write("No multi-scan-type hotspots found in this tile.\n")

        f.write("\n## Files\n\n")
        f.write("- `top_candidates.geojson` — top sites (open in QGIS or GitHub map)\n")
        f.write("- `top_candidates.csv` — same data, spreadsheet-friendly\n")
        f.write("- `hotspot_cluster/` — full multi-scan-type agreement analysis\n")
        f.write("- `*/anomaly.png` — visual heatmap per scan type\n")
        f.write(f"\n---\n*Generated {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}*\n")

    print(f"[report] {tile_id}: {len(sites)} sites "
          f"(best: {sites[0]['agreeing_types']}/{n_types} types)" if sites
          else f"[report] {tile_id}: 0 sites")
    print(f"  -> {md_out}")
    print(f"  -> {geojson_out}")
    print(f"  -> {csv_out}")
    return len(sites)


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
