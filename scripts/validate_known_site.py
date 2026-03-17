#!/usr/bin/env python3
"""
Validate that detection candidates cluster near a known archaeological site.
Reports how many candidates fall within 500m, 1km, 2km of that point.
Usage:
  python validate_known_site.py tile_30.8740_29.2470 --lon 30.899 --lat 29.267
  python validate_known_site.py tile_30.8740_29.2470  # uses sites.py lookup
"""
import json
import math
import os
import sys
import glob
import argparse


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    ap = argparse.ArgumentParser(description="Validate candidates near a known site")
    ap.add_argument("tile_id", help="Tile ID (e.g. tile_30.8740_29.2470)")
    ap.add_argument("--lon", type=float, default=None, help="Known site longitude")
    ap.add_argument("--lat", type=float, default=None, help="Known site latitude")
    ap.add_argument("--scan-type", default=None, help="Specific scan type to check (default: all)")
    args = ap.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(project_root, "results", args.tile_id)

    if not os.path.isdir(results_dir):
        print(f"Not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    known_lon, known_lat = args.lon, args.lat
    if known_lon is None or known_lat is None:
        sys.path.insert(0, os.path.join(project_root, "scripts"))
        try:
            from sites import SITES
            for sid, site in SITES.items():
                bbox = site["bbox"]
                center_lon = (bbox[0] + bbox[2]) / 2
                center_lat = (bbox[1] + bbox[3]) / 2
                if args.tile_id.startswith(f"tile_{bbox[0]:.4f}_{bbox[1]:.4f}"):
                    known_lon, known_lat = center_lon, center_lat
                    print(f"Using known site: {sid} ({site['name']}) center: {known_lon:.4f}, {known_lat:.4f}")
                    break
        except ImportError:
            pass
        if known_lon is None:
            print("Provide --lon and --lat, or ensure tile matches a site in sites.py", file=sys.stderr)
            sys.exit(1)

    if args.scan_type:
        geojson_paths = [os.path.join(results_dir, args.scan_type, "candidates.geojson")]
    else:
        geojson_paths = sorted(glob.glob(os.path.join(results_dir, "*", "candidates.geojson")))

    for geojson_path in geojson_paths:
        if not os.path.isfile(geojson_path):
            continue
        scan_type = os.path.basename(os.path.dirname(geojson_path))
        with open(geojson_path) as f:
            fc = json.load(f)
        coords = [
            (feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1])
            for feat in fc.get("features", [])
        ]
        total = len(coords)
        within_500m = sum(1 for lon, lat in coords if haversine_km(lon, lat, known_lon, known_lat) <= 0.5)
        within_1km = sum(1 for lon, lat in coords if haversine_km(lon, lat, known_lon, known_lat) <= 1.0)
        within_2km = sum(1 for lon, lat in coords if haversine_km(lon, lat, known_lon, known_lat) <= 2.0)
        print(f"\n{scan_type}: {total} candidates")
        print(f"  Within 500m: {within_500m}")
        print(f"  Within 1 km: {within_1km}")
        print(f"  Within 2 km: {within_2km}")
        if within_1km > 0:
            print("  -> Pipeline flags the known area.")
        else:
            print("  -> No candidates within 1 km of known site.")


if __name__ == "__main__":
    main()
