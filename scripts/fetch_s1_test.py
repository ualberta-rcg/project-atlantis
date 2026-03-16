#!/usr/bin/env python3
"""
Fetch a few Sentinel-1 images via CDSE Process API using only requests (no sentinelhub).
Use when sentinelhub/pyproj has env issues. Saves TIFFs (VV, VH, dataMask) for a test bbox and 3 time windows.
"""
import os
import sys
import json
import requests

# WGS84 bbox: min_lon, min_lat, max_lon, max_lat (small desert test area, Egypt)
TEST_BBOX = [29.9, 31.2, 30.1, 31.4]
# 3 time windows -> 3 images to compare
TIME_WINDOWS = [
    ("2023-01-01", "2023-01-15"),
    ("2023-06-01", "2023-06-15"),
    ("2023-12-01", "2023-12-15"),
]
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


def get_token(client_id: str, client_secret: str) -> str:
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def build_request(bbox: list, from_date: str, to_date: str, width: int = 512, height: int = 512):
    # API accepts bbox in WGS84 as [min_lon, min_lat, max_lon, max_lat] with crs 4326
    return {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [
                {
                    "type": "sentinel-1-grd",
                    "dataFilter": {
                        "timeRange": {"from": from_date + "T00:00:00Z", "to": to_date + "T23:59:59Z"},
                    },
                    "processing": {"orthorectify": "false"},
                }
            ],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
        },
        "evalscript": EVALSCRIPT,
    }


def main():
    client_id = os.environ.get("CDSE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "test_images")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output dir: {out_dir}")

    token = get_token(client_id, client_secret)
    print("Token obtained.")

    for i, (from_date, to_date) in enumerate(TIME_WINDOWS, 1):
        req = build_request(TEST_BBOX, from_date, to_date)
        r = requests.post(
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
            print(f"Request {i} failed: {r.status_code} {r.text[:500]}", file=sys.stderr)
            continue
        path = os.path.join(out_dir, f"s1_image_{i}_{from_date}_to_{to_date}.tif")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"Saved: {path} ({len(r.content)} bytes)")

    print("Done.")


if __name__ == "__main__":
    main()
