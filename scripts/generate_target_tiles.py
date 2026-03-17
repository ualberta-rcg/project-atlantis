#!/usr/bin/env python3
"""
Generate config/target_tiles.json by gridding a region. Each tile has
tile_id (from coords), bbox, and optional size_km/resolution_m.
"""
import argparse
import json
import os
import sys


def make_tile_id(min_lon, min_lat):
    return f"tile_{min_lon:.4f}_{min_lat:.4f}"


def generate_region(min_lon, max_lon, min_lat, max_lat, size_km, resolution_m):
    import math
    mid_lat = (min_lat + max_lat) / 2
    km_per_deg_lon = 111.0 * math.cos(math.radians(mid_lat))
    km_per_deg_lat = 111.0
    step_deg_lon = size_km / km_per_deg_lon
    step_deg_lat = size_km / km_per_deg_lat
    tiles = []
    lon = min_lon
    while lon < max_lon:
        lat = min_lat
        while lat < max_lat:
            max_lon_ = min(lon + step_deg_lon, max_lon)
            max_lat_ = min(lat + step_deg_lat, max_lat)
            tiles.append({
                "tile_id": make_tile_id(lon, lat),
                "bbox": [lon, lat, max_lon_, max_lat_],
                "size_km": size_km,
                "resolution_m": resolution_m,
            })
            lat += step_deg_lat
        lon += step_deg_lon
    return tiles


def main():
    ap = argparse.ArgumentParser(description="Generate target_tiles.json for a region or from config/scan.json")
    ap.add_argument("--min-lon", type=float, default=None)
    ap.add_argument("--max-lon", type=float, default=None)
    ap.add_argument("--min-lat", type=float, default=None)
    ap.add_argument("--max-lat", type=float, default=None)
    ap.add_argument("--from-scan", action="store_true", help="Use config/scan.json scan_regions and tile_defaults")
    ap.add_argument("--size-km", type=float, default=2.5, help="Tile side length in km")
    ap.add_argument("--resolution-m", type=float, default=10, help="Resolution in m/px")
    ap.add_argument("-o", "--output", default="config/target_tiles.json")
    args = ap.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = args.output if os.path.isabs(args.output) else os.path.join(project_root, args.output)

    if args.from_scan:
        scan_path = os.path.join(project_root, "config", "scan.json")
        if not os.path.isfile(scan_path):
            print("config/scan.json not found.", file=sys.stderr)
            sys.exit(1)
        with open(scan_path) as f:
            scan = json.load(f)
        defaults = scan.get("tile_defaults", {})
        size_km = defaults.get("size_km", 5)
        resolution_m = defaults.get("resolution_m", 10)
        all_tiles = []
        for region in scan.get("scan_regions", []):
            b = region.get("bounds", {})
            min_lon = b.get("min_lon")
            max_lon = b.get("max_lon")
            min_lat = b.get("min_lat")
            max_lat = b.get("max_lat")
            if None in (min_lon, max_lon, min_lat, max_lat):
                continue
            all_tiles.extend(generate_region(min_lon, max_lon, min_lat, max_lat, size_km, resolution_m))
        tiles = all_tiles
    else:
        if args.min_lon is None or args.max_lon is None or args.min_lat is None or args.max_lat is None:
            print("Either --from-scan or --min-lon --max-lon --min-lat --max-lat required.", file=sys.stderr)
            sys.exit(1)
        tiles = generate_region(args.min_lon, args.max_lon, args.min_lat, args.max_lat, args.size_km, args.resolution_m)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(tiles, f, indent=2)
    print(f"Wrote {out_path} ({len(tiles)} tiles)")


if __name__ == "__main__":
    main()
