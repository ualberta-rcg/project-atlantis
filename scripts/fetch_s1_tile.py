#!/usr/bin/env python3
"""
Fetch 2–5 Sentinel-1 images for a tile (tile_id + bbox) via CDSE Process API.
Writes GeoTIFFs to data/<tile_id>/. Same bbox and dimensions for all dates.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_s1_test import PROCESS_URL, TOKEN_URL, get_token, build_request

# Default time windows if not in pipeline.json
DEFAULT_TIME_WINDOWS = [
    ("2023-01-01", "2023-01-15"),
    ("2023-06-01", "2023-06-15"),
    ("2023-12-01", "2023-12-15"),
]


def main():
    import argparse
    import json
    ap = argparse.ArgumentParser(description="Fetch S1 images for a tile (bbox)")
    ap.add_argument("tile_id", help="Tile identifier")
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("min_lon", "min_lat", "max_lon", "max_lat"), required=True)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--size", type=int, default=None, help="Width/height in pixels (default from pipeline.json or 250)")
    ap.add_argument("--time-windows", nargs="+", default=None, help="Pairs: from to from to ...")
    args = ap.parse_args()

    client_id = os.environ.get("CDSE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET", file=sys.stderr)
        sys.exit(1)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = args.data_dir or os.path.join(project_root, "data")
    out_dir = os.path.join(data_dir, args.tile_id)
    os.makedirs(out_dir, exist_ok=True)

    size = args.size
    if size is None:
        pipeline_path = os.path.join(project_root, "config", "pipeline.json")
        if os.path.isfile(pipeline_path):
            with open(pipeline_path) as f:
                pl = json.load(f)
            res_m = pl.get("default_resolution_m", 10)
            size_km = pl.get("default_size_km", 2.5)
            size = int(size_km * 1000 / res_m)
        else:
            size = 250

    if args.time_windows and len(args.time_windows) % 2 == 0:
        time_windows = [(args.time_windows[i], args.time_windows[i+1]) for i in range(0, len(args.time_windows), 2)]
    else:
        time_windows = DEFAULT_TIME_WINDOWS

    bbox = list(args.bbox)
    token = get_token(client_id, client_secret)
    paths = []
    for from_date, to_date in time_windows:
        req = build_request(bbox, from_date, to_date, width=size, height=size)
        r = __import__("requests").post(
            PROCESS_URL,
            json=req,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "image/tiff"},
            timeout=120,
        )
        if r.status_code != 200:
            print(f"Request failed {r.status_code}: {r.text[:200]}", file=sys.stderr)
            continue
        path = os.path.join(out_dir, f"s1_{from_date}_to_{to_date}.tif")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"Saved: {path}")
        paths.append(path)
    if not paths:
        print("No images saved.", file=sys.stderr)
        sys.exit(1)
    print(f"Done. {len(paths)} images.")


if __name__ == "__main__":
    main()
