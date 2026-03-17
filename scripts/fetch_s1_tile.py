#!/usr/bin/env python3
"""
Fetch Sentinel-1 GRD images for a tile via CDSE Process API (v3).
Generates evenly-spaced time windows across the configured time range,
fetches one image per window (default 500x500 for 5km at 10m).
Writes GeoTIFFs to results/<tile_id>/raw/. Same bbox and dimensions for all dates.
"""
import os
import sys
import json
import argparse
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["VV", "VH", "dataMask"],
    output: { id: "default", bands: 3, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [sample.VV, sample.VH, sample.dataMask];
}
"""


def get_token(client_id, client_secret):
    r = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def build_request(bbox, from_date, to_date, width=500, height=500):
    return {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [{
                "type": "sentinel-1-grd",
                "dataFilter": {
                    "timeRange": {"from": from_date + "T00:00:00Z", "to": to_date + "T23:59:59Z"},
                    "mosaickingOrder": "mostRecent",
                },
                "processing": {"orthorectify": "true", "backCoeff": "SIGMA0_ELLIPSOID"},
            }],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
        },
        "evalscript": EVALSCRIPT,
    }


def generate_time_windows(start_year=2019, end_year=2026, num_images=12):
    """Generate evenly-spaced 2-week time windows across the date range."""
    from datetime import date, timedelta
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    total_days = (end - start).days
    step = total_days // num_images
    windows = []
    for i in range(num_images):
        d = start + timedelta(days=i * step)
        d_end = d + timedelta(days=14)
        windows.append((d.isoformat(), d_end.isoformat()))
    return windows


def main():
    ap = argparse.ArgumentParser(description="Fetch S1 images for a tile (v3)")
    ap.add_argument("tile_id", help="Tile identifier")
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("min_lon", "min_lat", "max_lon", "max_lat"), required=True)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--size", type=int, default=None, help="Width/height in pixels")
    ap.add_argument("--num-images", type=int, default=None, help="Number of images to fetch")
    ap.add_argument("--time-windows", nargs="+", default=None, help="Pairs: from to from to ...")
    args = ap.parse_args()

    client_id = os.environ.get("CDSE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET", file=sys.stderr)
        sys.exit(1)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = args.data_dir or os.path.join(project_root, "results")
    out_dir = os.path.join(data_dir, args.tile_id, "raw")
    os.makedirs(out_dir, exist_ok=True)

    scan_path = os.path.join(project_root, "config", "scan.json")
    scan_config = {}
    if os.path.isfile(scan_path):
        with open(scan_path) as f:
            scan_config = json.load(f)

    tile_defaults = scan_config.get("tile_defaults", {})
    imagery = scan_config.get("imagery", {})

    size = args.size
    if size is None:
        size_km = tile_defaults.get("size_km", 5)
        res_m = tile_defaults.get("resolution_m", 10)
        size = int(size_km * 1000 / res_m)

    num_images = args.num_images or imagery.get("preferred_images", 12)

    if args.time_windows and len(args.time_windows) % 2 == 0:
        time_windows = [(args.time_windows[i], args.time_windows[i + 1]) for i in range(0, len(args.time_windows), 2)]
    else:
        tw = imagery.get("time_window", "2019-01-01/2026-12-31")
        start_year = int(tw.split("/")[0][:4])
        end_year = int(tw.split("/")[1][:4])
        time_windows = generate_time_windows(start_year, end_year, num_images)

    bbox = list(args.bbox)
    print(f"Fetching {len(time_windows)} images for {args.tile_id} at {size}x{size} px")
    print(f"Bbox: {bbox}")

    token = get_token(client_id, client_secret)
    print("Token obtained.")

    paths = []
    for i, (from_date, to_date) in enumerate(time_windows, 1):
        req = build_request(bbox, from_date, to_date, width=size, height=size)
        print(f"  [{i}/{len(time_windows)}] {from_date} to {to_date} ...", end=" ", flush=True)
        r = requests.post(
            PROCESS_URL,
            json=req,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "image/tiff"},
            timeout=180,
        )
        if r.status_code != 200:
            print(f"FAILED {r.status_code}: {r.text[:200]}")
            continue
        path = os.path.join(out_dir, f"s1_{from_date}_to_{to_date}.tif")
        with open(path, "wb") as f:
            f.write(r.content)
        sz_mb = len(r.content) / 1024 / 1024
        print(f"OK ({sz_mb:.1f} MB)")
        paths.append(path)

    if not paths:
        print("No images saved.", file=sys.stderr)
        sys.exit(1)
    print(f"Done. {len(paths)} images saved to {out_dir}")


if __name__ == "__main__":
    main()
