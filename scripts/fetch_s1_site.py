#!/usr/bin/env python3
"""
Fetch Sentinel-1 images for a named site via CDSE Process API.
Uses scripts/sites.py for bbox. Writes GeoTIFFs to results/<site_id>/raw/.
"""
import os
import sys

# Add script dir so we can import sites
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sites import SITES, DEFAULT_TIME_WINDOWS

from fetch_s1_test import (
    PROCESS_URL,
    TOKEN_URL,
    EVALSCRIPT,
    get_token,
    build_request,
)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Fetch S1 images for a site")
    ap.add_argument("site_id", choices=list(SITES.keys()), help="Site key from sites.py")
    ap.add_argument("--data-dir", default=None, help="Base data dir (default: project root / data)")
    ap.add_argument("--time-windows", nargs="+", default=None,
                    help="Override dates, e.g. 2023-01-01 2023-01-15 2023-06-01 2023-06-15")
    ap.add_argument("--size", type=int, default=512)
    args = ap.parse_args()

    client_id = os.environ.get("CDSE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET", file=sys.stderr)
        sys.exit(1)

    site = SITES[args.site_id]
    bbox = site["bbox"]
    if args.data_dir:
        out_dir = os.path.join(args.data_dir, args.site_id, "raw")
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.path.join(project_root, "results", args.site_id, "raw")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Site: {args.site_id} ({site['name']})")
    print(f"Bbox: {bbox}")
    print(f"Output: {out_dir}")

    if args.time_windows:
        if len(args.time_windows) % 2 != 0:
            print("--time-windows must be pairs: from to from to ...", file=sys.stderr)
            sys.exit(1)
        time_windows = [(args.time_windows[i], args.time_windows[i+1]) for i in range(0, len(args.time_windows), 2)]
    else:
        time_windows = DEFAULT_TIME_WINDOWS

    token = get_token(client_id, client_secret)
    paths = []
    for i, (from_date, to_date) in enumerate(time_windows, 1):
        req = build_request(bbox, from_date, to_date, width=args.size, height=args.size)
        r = __import__("requests").post(
            PROCESS_URL,
            json=req,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "image/tiff",
            },
            timeout=120,
        )
        if r.status_code != 200:
            print(f"Request {i} failed: {r.status_code} {r.text[:300]}", file=sys.stderr)
            continue
        path = os.path.join(out_dir, f"s1_{from_date}_to_{to_date}.tif")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"Saved: {path}")
        paths.append(path)
    if not paths:
        print("No images saved.", file=sys.stderr)
        sys.exit(1)
    print(f"Done. {len(paths)} images. Use stack_timeseries.py on these for next step.")


if __name__ == "__main__":
    main()
