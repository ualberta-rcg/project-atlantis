#!/usr/bin/env python3
"""
Request Sentinel-1 GRD backscatter (VV, VH) by bbox and time from the
Copernicus Data Space Ecosystem (CDSE) Process API. No full-product download.

Usage:
  Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET in the environment (or pass --client-id/--client-secret).
  Example:
    export CDSE_CLIENT_ID=...
    export CDSE_CLIENT_SECRET=...
    python request_sentinel1_cdse.py --bbox 15.4 46.7 15.6 46.9 --time 2023-01-01 2023-01-31 --resolution 20 --out s1_tile.npy

  For Slurm job arrays: call with different --bbox or tile ID; add a short delay between jobs to respect 300 req/min.
"""

import argparse
import os
import sys


def get_cdse_config():
    """Build SHConfig for Copernicus Data Space Ecosystem."""
    try:
        from sentinelhub import SHConfig
    except ImportError:
        sys.exit("Install sentinelhub: pip install sentinelhub")

    config = SHConfig()
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    config.sh_client_id = os.environ.get("CDSE_CLIENT_ID", "")
    config.sh_client_secret = os.environ.get("CDSE_CLIENT_SECRET", "")
    return config


# Evalscript: return VV, VH (linear power), and dataMask for Sentinel-1 GRD.
# Values are in linear power; convert to dB in post if needed: 10 * log10(linear).
EVALSCRIPT_S1_BACKSCATTER = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["VV", "VH", "dataMask"]
    }],
    output: {
      bands: 3,
      sampleType: "FLOAT32"
    }
  };
}
function evaluatePixel(sample) {
  return [sample.VV, sample.VH, sample.dataMask];
}
"""


def request_s1_bbox(bbox_coords, time_interval, resolution_m, config, client_id=None, client_secret=None):
    """
    Request Sentinel-1 (VV, VH) for a bbox and time range via CDSE Process API.

    bbox_coords: (min_lon, min_lat, max_lon, max_lat) in WGS84
    time_interval: (start_date, end_date) e.g. ("2023-01-01", "2023-01-31")
    resolution_m: output resolution in metres (e.g. 20)
    config: SHConfig with sh_base_url and sh_token_url set for CDSE

    Returns list of numpy arrays (one per acquisition/mosaic); each array shape (H, W, 3) with VV, VH, dataMask.
    """
    from sentinelhub import (
        BBox,
        CRS,
        DataCollection,
        MimeType,
        SentinelHubRequest,
        bbox_to_dimensions,
    )

    if client_id:
        config.sh_client_id = client_id
    if client_secret:
        config.sh_client_secret = client_secret
    if not config.sh_client_id or not config.sh_client_secret:
        raise ValueError("CDSE credentials missing. Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET or pass --client-id/--client-secret")

    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    size = bbox_to_dimensions(bbox, resolution=resolution_m)

    s1_collection = DataCollection.SENTINEL1_IW.define_from(
        "s1grd_iw", service_url=config.sh_base_url
    )

    request = SentinelHubRequest(
        evalscript=EVALSCRIPT_S1_BACKSCATTER,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=s1_collection,
                time_interval=time_interval,
                other_args={"dataFilter": {"mosaickingOrder": "mostRecent"}},
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config,
    )
    data = request.get_data()
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Request Sentinel-1 backscatter by bbox from CDSE Process API"
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("min_lon", "min_lat", "max_lon", "max_lat"),
        required=True,
        help="Bounding box in WGS84 (min_lon min_lat max_lon max_lat)",
    )
    parser.add_argument(
        "--time",
        type=str,
        nargs=2,
        metavar=("START", "END"),
        required=True,
        help="Time interval, e.g. 2023-01-01 2023-01-31",
    )
    parser.add_argument(
        "--resolution",
        type=float,
        default=20,
        help="Output resolution in metres (default 20)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="Output path: .npy (numpy) or .tif (GeoTIFF if rasterio available). Default: print shape and exit.",
    )
    parser.add_argument(
        "--client-id",
        type=str,
        default=os.environ.get("CDSE_CLIENT_ID", ""),
        help="CDSE OAuth client ID (or set CDSE_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        type=str,
        default=os.environ.get("CDSE_CLIENT_SECRET", ""),
        help="CDSE OAuth client secret (or set CDSE_CLIENT_SECRET)",
    )
    args = parser.parse_args()

    config = get_cdse_config()
    if args.client_id:
        config.sh_client_id = args.client_id
    if args.client_secret:
        config.sh_client_secret = args.client_secret

    bbox = tuple(args.bbox)
    time_interval = (args.time[0], args.time[1])

    try:
        data = request_s1_bbox(bbox, time_interval, args.resolution, config)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not data:
        print("No data returned for this bbox/time.", file=sys.stderr)
        sys.exit(1)

    arr = data[0]
    print(f"Shape: {arr.shape} (H, W, 3) -> VV, VH, dataMask")

    if args.out:
        if args.out.endswith(".npy"):
            import numpy as np
            np.save(args.out, arr)
            print(f"Saved: {args.out}")
        elif args.out.endswith(".tif") or args.out.endswith(".tiff"):
            try:
                import rasterio
                from rasterio.crs import CRS as RasterioCRS
                from rasterio.transform import from_bounds
                h, w = arr.shape[0], arr.shape[1]
                min_lon, min_lat, max_lon, max_lat = bbox
                transform = from_bounds(min_lon, min_lat, max_lon, max_lat, w, h)
                with rasterio.open(
                    args.out,
                    "w",
                    driver="GTiff",
                    height=h,
                    width=w,
                    count=3,
                    dtype=arr.dtype,
                    crs=RasterioCRS.from_epsg(4326),
                    transform=transform,
                ) as dst:
                    dst.write(arr[:, :, 0], 1)
                    dst.write(arr[:, :, 1], 2)
                    dst.write(arr[:, :, 2], 3)
                print(f"Saved: {args.out}")
            except ImportError:
                print("rasterio not installed; saving as .npy instead.", file=sys.stderr)
                args.out_npy = args.out.rsplit(".", 1)[0] + ".npy"
                import numpy as np
                np.save(args.out_npy, arr)
                print(f"Saved: {args.out_npy}")
        else:
            import numpy as np
            np.save(args.out + ".npy" if not args.out.endswith(".npy") else args.out, arr)
            print(f"Saved: {args.out}.npy" if not args.out.endswith(".npy") else args.out)


if __name__ == "__main__":
    main()
