#!/usr/bin/env python3
"""
Build temporal stack from S1 GeoTIFFs (same bbox/size). Output: 8 bands for v3 scan types.
Bands: mean_VV, mean_VH, var_VV, var_VH, std_VV, std_VH, median_VV, median_VH.
Existing stack_timeseries.py outputs 4 bands; this extends with std and median for CV, MAD, etc.
"""
import argparse
import numpy as np
import os

try:
    import rasterio
except ImportError:
    rasterio = None


def build_stack(tif_paths, out_path, nodata=np.nan):
    if not tif_paths:
        raise ValueError("No input TIFFs")
    if rasterio is None:
        raise ImportError("rasterio is required")

    arrays = []
    ref_profile = None
    for p in tif_paths:
        with rasterio.open(p) as src:
            if ref_profile is None:
                ref_profile = src.profile.copy()
            vv = src.read(1)
            vh = src.read(2)
            mask = src.read(3)
            arrays.append((vv, vh, mask))

    vv_stack = np.array([a[0] for a in arrays], dtype=np.float64)
    vh_stack = np.array([a[1] for a in arrays], dtype=np.float64)
    mask_stack = np.array([a[2] for a in arrays], dtype=np.float64)
    valid = np.nanmean(mask_stack, axis=0) > 0.5
    vv_stack[~np.broadcast_to(valid, vv_stack.shape)] = np.nan
    vh_stack[~np.broadcast_to(valid, vh_stack.shape)] = np.nan

    mean_vv = np.nanmean(vv_stack, axis=0)
    mean_vh = np.nanmean(vh_stack, axis=0)
    var_vv = np.nanvar(vv_stack, axis=0)
    var_vh = np.nanvar(vh_stack, axis=0)
    std_vv = np.nanstd(vv_stack, axis=0)
    std_vh = np.nanstd(vh_stack, axis=0)
    median_vv = np.nanmedian(vv_stack, axis=0)
    median_vh = np.nanmedian(vh_stack, axis=0)

    def to_out(x):
        return np.where(np.isfinite(x), x.astype(np.float32), nodata)

    profile = ref_profile.copy()
    profile.update(count=8, dtype=np.float32, nodata=nodata)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(to_out(mean_vv), 1)
        dst.write(to_out(mean_vh), 2)
        dst.write(to_out(var_vv), 3)
        dst.write(to_out(var_vh), 4)
        dst.write(to_out(std_vv), 5)
        dst.write(to_out(std_vh), 6)
        dst.write(to_out(median_vv), 7)
        dst.write(to_out(median_vh), 8)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Build 8-band stack (mean/var/std/median VV+VH)")
    ap.add_argument("tifs", nargs="+", help="Input GeoTIFF paths")
    ap.add_argument("-o", "--output", required=True, help="Output stack GeoTIFF")
    args = ap.parse_args()
    build_stack(args.tifs, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
