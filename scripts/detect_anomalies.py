#!/usr/bin/env python3
"""
Read stack GeoTIFF (bands: mean_VV, mean_VH, var_VV, var_VH). Compute anomaly score
(e.g. variance-based), threshold to get candidate pixels, convert to lon/lat,
write candidates.csv, candidates.geojson, and anomaly.tif.
"""
import argparse
import json
import os
import sys
from datetime import datetime

import numpy as np

try:
    import rasterio
    from rasterio.transform import xy
except ImportError:
    rasterio = None


def detect_anomalies(
    stack_path,
    out_dir,
    score_band="variance",  # "variance" = use var_VV + var_VH; or "mean" for mean-based
    percentile_threshold=95,
    min_score=None,
    site_id="",
    pathway=None,
):
    """
    stack_path: path to stack GeoTIFF (4 bands: mean_VV, mean_VH, var_VV, var_VH)
    out_dir: where to write candidates.csv, candidates.geojson, anomaly.tif, metadata.json
    score_band: "variance" -> score = var_VV + var_VH; "vv" -> var_VV only; "vh" -> var_VH only
    percentile_threshold: keep pixels with score >= this percentile (default 95 = top 5%)
    min_score: if set, also require score >= min_score (absolute)
    """
    if rasterio is None:
        raise ImportError("rasterio required: pip install rasterio")

    os.makedirs(out_dir, exist_ok=True)

    with rasterio.open(stack_path) as src:
        profile = src.profile.copy()
        transform = src.transform
        mean_vv = src.read(1)
        mean_vh = src.read(2)
        var_vv = src.read(3)
        var_vh = src.read(4)
        nodata = src.nodata
        h, w = mean_vv.shape

    # Anomaly score: higher variance = more change over time = candidate
    if score_band == "variance":
        score = np.float64(var_vv) + np.float64(var_vh)
    elif score_band == "vv":
        score = np.float64(var_vv)
    elif score_band == "vh":
        score = np.float64(var_vh)
    else:
        score = np.float64(var_vv) + np.float64(var_vh)

    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (mean_vv != nodata) & (mean_vh != nodata)
    score[~valid] = np.nan

    # Threshold
    thresh = np.nanpercentile(score[valid], percentile_threshold) if np.any(valid) else 0
    if min_score is not None:
        thresh = max(thresh, min_score)
    candidates_mask = valid & (score >= thresh)

    # Pixel indices of candidates
    rows, cols = np.where(candidates_mask)
    scores = score[rows, cols]
    # "Chance" 0-1: how far above threshold (0 = at threshold, 1 = max score in scene)
    score_max = np.nanmax(score[valid]) if np.any(valid) else thresh
    if score_max > thresh:
        chances = (scores - thresh) / (score_max - thresh)
    else:
        chances = np.ones_like(scores)

    # Pixel -> lon, lat (center of pixel)
    lons, lats = [], []
    for r, c in zip(rows, cols):
        lon, lat = xy(transform, r, c, offset="center")
        lons.append(float(lon))
        lats.append(float(lat))

    # Write anomaly raster (score map)
    profile.update(count=1, dtype=np.float32, nodata=np.nan)
    anomaly_path = os.path.join(out_dir, "anomaly.tif")
    with rasterio.open(anomaly_path, "w", **profile) as dst:
        out_score = np.where(valid, score.astype(np.float32), np.nan)
        dst.write(out_score, 1)
    print(f"Wrote {anomaly_path}")

    # CSV (chance = 0-1; tile_id = site_id per plan; pathway optional)
    csv_path = os.path.join(out_dir, "candidates.csv")
    tile_id = site_id  # plan uses tile_id
    with open(csv_path, "w") as f:
        if pathway:
            f.write("lon,lat,score,chance,tile_id,pathway\n")
            for lon, lat, s, ch in zip(lons, lats, scores, chances):
                f.write(f"{lon},{lat},{s:.6e},{ch:.4f},{tile_id},{pathway}\n")
        else:
            f.write("lon,lat,score,chance,tile_id\n")
            for lon, lat, s, ch in zip(lons, lats, scores, chances):
                f.write(f"{lon},{lat},{s:.6e},{ch:.4f},{tile_id}\n")
    print(f"Wrote {csv_path} ({len(lons)} candidates)")

    # GeoJSON (chance = 0-1; tile_id and optional pathway per plan)
    geojson_path = os.path.join(out_dir, "candidates.geojson")
    features = []
    for lon, lat, s, ch in zip(lons, lats, scores, chances):
        props = {"lon": lon, "lat": lat, "score": float(s), "chance": float(ch), "tile_id": tile_id}
        if pathway:
            props["pathway"] = pathway
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        })
    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }
    with open(geojson_path, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"Wrote {geojson_path}")

    # Metadata
    meta_path = os.path.join(out_dir, "metadata.json")
    meta = {
        "stack_path": os.path.abspath(stack_path),
        "tile_id": tile_id,
        "site_id": site_id,
        "pathway": pathway,
        "bbox": None,  # caller can add
        "date_range": None,
        "run_time_seconds": None,
        "percentile_threshold": percentile_threshold,
        "candidate_count": len(lons),
        "min_score": min_score,
        "threshold_used": float(thresh),
        "num_candidates": len(lons),
        "chance_meaning": "0-1: how far above variance threshold (higher = more anomalous, not InSAR displacement)",
        "method": "temporal variance of backscatter (VV+VH over 2-5 dates); no InSAR/coherence/displacement",
        "run_time_utc": datetime.utcnow().isoformat() + "Z",
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {meta_path}")

    return len(lons), thresh


def main():
    ap = argparse.ArgumentParser(description="Detect anomaly candidates from stack")
    ap.add_argument("stack", help="Stack GeoTIFF (mean_VV, mean_VH, var_VV, var_VH)")
    ap.add_argument("-o", "--out-dir", required=True, help="Output directory")
    ap.add_argument("--site-id", default="", help="Site/tile identifier for CSV/GeoJSON")
    ap.add_argument("--pathway", default=None, help="Pathway name (e.g. variance_95) for output properties")
    ap.add_argument("--score", choices=["variance", "vv", "vh"], default="variance")
    ap.add_argument("--percentile", type=float, default=95)
    ap.add_argument("--min-score", type=float, default=None)
    args = ap.parse_args()
    detect_anomalies(
        args.stack,
        args.out_dir,
        score_band=args.score,
        percentile_threshold=args.percentile,
        min_score=args.min_score,
        site_id=args.site_id,
        pathway=args.pathway,
    )


if __name__ == "__main__":
    main()
