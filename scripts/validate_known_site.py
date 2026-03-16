#!/usr/bin/env python3
"""
Validate that detection candidates cluster near a known archaeological site.
Known location: Qubbet el-Hawa tombs ~ 32.889158°E, 24.101769°N (lon, lat).
Reports how many candidates fall within 500m, 1km, 2km of that point.
"""
import json
import math
import os
import sys

# Qubbet el-Hawa (from GeoHack / literature)
KNOWN_LON, KNOWN_LAT = 32.889158, 24.101769


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results", "qubbet_el_hawa")
    geojson_path = os.path.join(results_dir, "candidates.geojson")
    if not os.path.isfile(geojson_path):
        print(f"Not found: {geojson_path}", file=sys.stderr)
        sys.exit(1)
    with open(geojson_path) as f:
        fc = json.load(f)
    coords = [
        (f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1])
        for f in fc["features"]
    ]
    total = len(coords)
    within_500m = sum(1 for lon, lat in coords if haversine_km(lon, lat, KNOWN_LON, KNOWN_LAT) <= 0.5)
    within_1km = sum(1 for lon, lat in coords if haversine_km(lon, lat, KNOWN_LON, KNOWN_LAT) <= 1.0)
    within_2km = sum(1 for lon, lat in coords if haversine_km(lon, lat, KNOWN_LON, KNOWN_LAT) <= 2.0)
    print("Validation: Qubbet el-Hawa (known tombs at 32.889°E, 24.102°N)")
    print(f"  Total candidates: {total}")
    print(f"  Within 500m of known site: {within_500m}")
    print(f"  Within 1 km:              {within_1km}")
    print(f"  Within 2 km:              {within_2km}")
    if within_1km > 0:
        print("  -> Pipeline flags the known area (candidates cluster near tombs).")
    else:
        print("  -> No candidates within 1 km; check bbox or detection threshold.")


if __name__ == "__main__":
    main()
