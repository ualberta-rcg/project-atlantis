#!/usr/bin/env python3
"""
Generate PNG previews for all GeoTIFFs in a tile results directory.
Walks results/<tile_id>/ and creates a .png beside every .tif.
Usage:
  python generate_pngs.py results/tile_30.8740_29.2470
  python generate_pngs.py /tmp/workdir/tile_30.8740_29.2470
"""
import os
import sys
import glob
import numpy as np

try:
    import rasterio
except ImportError:
    rasterio = None

try:
    from PIL import Image
except ImportError:
    Image = None


def normalize_band(arr):
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return np.zeros_like(arr, dtype=np.uint8)
    lo, hi = np.percentile(valid, [2, 98])
    if hi <= lo:
        hi = lo + 1
    clipped = np.clip(arr, lo, hi)
    return ((clipped - lo) / (hi - lo) * 255).astype(np.uint8)


def tif_to_png(tif_path, png_path=None):
    if rasterio is None or Image is None:
        return None
    if png_path is None:
        png_path = tif_path.rsplit(".", 1)[0] + ".png"
    try:
        with rasterio.open(tif_path) as src:
            bands = src.count
            if bands >= 3:
                r = normalize_band(src.read(1).astype(np.float64))
                g = normalize_band(src.read(2).astype(np.float64))
                b = normalize_band(src.read(1).astype(np.float64))
                img = Image.fromarray(np.stack([r, g, b], axis=-1))
            elif bands == 2:
                r = normalize_band(src.read(1).astype(np.float64))
                g = normalize_band(src.read(2).astype(np.float64))
                b = np.zeros_like(r)
                img = Image.fromarray(np.stack([r, g, b], axis=-1))
            else:
                arr = normalize_band(src.read(1).astype(np.float64))
                img = Image.fromarray(arr, mode="L")
        img.save(png_path)
        return png_path
    except Exception as e:
        print(f"  Warning: PNG failed for {tif_path}: {e}", file=sys.stderr)
        return None


def generate_all_pngs(tile_dir):
    tifs = sorted(glob.glob(os.path.join(tile_dir, "**", "*.tif"), recursive=True))
    created = 0
    for tif in tifs:
        png = tif.rsplit(".", 1)[0] + ".png"
        if os.path.exists(png) and os.path.getmtime(png) >= os.path.getmtime(tif):
            continue
        result = tif_to_png(tif, png)
        if result:
            created += 1
    return created


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_pngs.py <tile_dir> [tile_dir2 ...]", file=sys.stderr)
        sys.exit(1)
    if rasterio is None:
        print("rasterio required", file=sys.stderr)
        sys.exit(1)
    if Image is None:
        print("Pillow required", file=sys.stderr)
        sys.exit(1)
    total = 0
    for d in sys.argv[1:]:
        n = generate_all_pngs(d)
        total += n
        print(f"{d}: {n} PNGs generated")
    print(f"Total: {total} PNGs")


if __name__ == "__main__":
    main()
