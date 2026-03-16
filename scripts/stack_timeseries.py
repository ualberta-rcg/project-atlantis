#!/usr/bin/env python3
"""
Read 2–5 Sentinel-1 GeoTIFFs (same bbox/size), compute temporal mean and variance
for VV and VH (bands 0 and 1). Writes one stack GeoTIFF: mean_VV, mean_VH, var_VV, var_VH.
Band 2 (dataMask) is averaged and used to mask invalid pixels.
"""
import argparse
import numpy as np
import os

try:
    import rasterio
    from rasterio.transform import from_bounds
except ImportError:
    rasterio = None


def stack_timeseries(tif_paths, out_path, nodata=np.nan):
    if not tif_paths:
        raise ValueError("No input TIFFs")
    if rasterio is None:
        raise ImportError("rasterio is required: pip install rasterio")

    arrays = []
    ref_profile = None
    ref_bounds = None
    for p in tif_paths:
        with rasterio.open(p) as src:
            if ref_profile is None:
                ref_profile = src.profile.copy()
                ref_bounds = src.bounds
            # Read bands 0 (VV), 1 (VH), 2 (dataMask)
            vv = src.read(1)
            vh = src.read(2)
            mask = src.read(3)
            arrays.append((vv, vh, mask))

    # Stack: (N, H, W) each
    vv_stack = np.array([a[0] for a in arrays], dtype=np.float64)
    vh_stack = np.array([a[1] for a in arrays], dtype=np.float64)
    mask_stack = np.array([a[2] for a in arrays], dtype=np.float64)

    # Mask invalid (no data)
    valid = np.nanmean(mask_stack, axis=0) > 0.5
    vv_stack[~np.broadcast_to(valid, vv_stack.shape)] = np.nan
    vh_stack[~np.broadcast_to(valid, vh_stack.shape)] = np.nan

    mean_vv = np.nanmean(vv_stack, axis=0)
    mean_vh = np.nanmean(vh_stack, axis=0)
    var_vv = np.nanvar(vv_stack, axis=0)
    var_vh = np.nanvar(vh_stack, axis=0)
    # Replace nan with nodata for writing
    mean_vv = np.where(np.isfinite(mean_vv), mean_vv, nodata)
    mean_vh = np.where(np.isfinite(mean_vh), mean_vh, nodata)
    var_vv = np.where(np.isfinite(var_vv), var_vv, nodata)
    var_vh = np.where(np.isfinite(var_vh), var_vh, nodata)

    profile = ref_profile.copy()
    profile.update(count=4, dtype=np.float32, nodata=nodata)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(mean_vv.astype(np.float32), 1)
        dst.write(mean_vh.astype(np.float32), 2)
        dst.write(var_vv.astype(np.float32), 3)
        dst.write(var_vh.astype(np.float32), 4)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Stack S1 GeoTIFFs -> mean and variance")
    ap.add_argument("tifs", nargs="+", help="Input GeoTIFF paths (same bbox/size)")
    ap.add_argument("-o", "--output", required=True, help="Output stack GeoTIFF")
    ap.add_argument("--nodata", type=float, default=np.nan, help="Nodata value (default nan)")
    args = ap.parse_args()
    stack_timeseries(args.tifs, args.output, nodata=args.nodata)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
