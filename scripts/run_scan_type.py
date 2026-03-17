#!/usr/bin/env python3
"""
Run a single scan type on an existing stack. Used by run_pipeline after build_stack.
Usage: run_scan_type.py <stack_path> <scan_type_name> <output_dir> [tile_id]

Stack bands: 1=mean_VV, 2=mean_VH, 3=var_VV, 4=var_VH, 5=std_VV, 6=std_VH, 7=median_VV, 8=median_VH
"""
import os
import sys
import json
import numpy as np
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
SCAN_CONFIG_PATH = os.path.join(CONFIG_DIR, "scan.json")

try:
    import rasterio
    from rasterio.transform import xy
except ImportError:
    rasterio = None


def load_scan_config():
    if not os.path.isfile(SCAN_CONFIG_PATH):
        return {}
    with open(SCAN_CONFIG_PATH) as f:
        return json.load(f)


def read_stack(stack_path):
    with rasterio.open(stack_path) as src:
        bands = {}
        bands["mean_vv"] = src.read(1).astype(np.float64)
        bands["mean_vh"] = src.read(2).astype(np.float64)
        bands["var_vv"] = src.read(3).astype(np.float64)
        bands["var_vh"] = src.read(4).astype(np.float64)
        if src.count >= 6:
            bands["std_vv"] = src.read(5).astype(np.float64)
            bands["std_vh"] = src.read(6).astype(np.float64)
        else:
            bands["std_vv"] = np.sqrt(np.maximum(bands["var_vv"], 0))
            bands["std_vh"] = np.sqrt(np.maximum(bands["var_vh"], 0))
        if src.count >= 8:
            bands["median_vv"] = src.read(7).astype(np.float64)
            bands["median_vh"] = src.read(8).astype(np.float64)
        else:
            bands["median_vv"] = bands["mean_vv"].copy()
            bands["median_vh"] = bands["mean_vh"].copy()
        profile = src.profile.copy()
        transform = src.transform
        nodata = src.nodata
    return bands, profile, transform, nodata


def threshold_and_output(score, valid, percentile, output_dir, profile, transform, tile_id, scan_type_name):
    """Common logic: threshold score array, write anomaly.tif, candidates, metadata."""
    os.makedirs(output_dir, exist_ok=True)
    score[~valid] = np.nan
    thresh = np.nanpercentile(score[valid], percentile) if np.any(valid) else 0
    cand_mask = valid & (score >= thresh)
    rows, cols = np.where(cand_mask)
    scores = score[rows, cols]
    score_max = np.nanmax(score[valid]) if np.any(valid) else thresh
    if score_max > thresh:
        chances = (scores - thresh) / (score_max - thresh)
    else:
        chances = np.ones_like(scores)

    lons, lats = [], []
    for r, c in zip(rows, cols):
        lon, lat = xy(transform, r, c, offset="center")
        lons.append(float(lon))
        lats.append(float(lat))

    # anomaly.tif
    p = profile.copy()
    p.update(count=1, dtype=np.float32, nodata=np.nan)
    with rasterio.open(os.path.join(output_dir, "anomaly.tif"), "w", **p) as dst:
        dst.write(np.where(valid, score.astype(np.float32), np.nan), 1)

    # candidates.csv
    with open(os.path.join(output_dir, "candidates.csv"), "w") as f:
        f.write("lon,lat,score,chance,tile_id,pathway\n")
        for lon, lat, s, ch in zip(lons, lats, scores, chances):
            f.write(f"{lon},{lat},{s:.6e},{ch:.4f},{tile_id},{scan_type_name}\n")

    # candidates.geojson
    features = []
    for lon, lat, s, ch in zip(lons, lats, scores, chances):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"lon": lon, "lat": lat, "score": float(s), "chance": float(ch),
                           "tile_id": tile_id, "pathway": scan_type_name},
        })
    with open(os.path.join(output_dir, "candidates.geojson"), "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

    # metadata.json
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump({
            "scan_type": scan_type_name, "tile_id": tile_id,
            "percentile_threshold": percentile, "threshold_used": float(thresh),
            "num_candidates": len(lons), "candidate_count": len(lons),
            "run_time_utc": datetime.utcnow().isoformat() + "Z",
        }, f, indent=2)

    print(f"  {scan_type_name}: {len(lons)} candidates (threshold={thresh:.6e})")
    return len(lons)


def run_temporal_variance(stack_path, output_dir, config, tile_id):
    sys.path.insert(0, SCRIPT_DIR)
    from scan_types.temporal_variance import run
    return run(stack_path, None, output_dir, config, tile_id=tile_id)


def run_temporal_cv(stack_path, output_dir, config, tile_id):
    bands, profile, transform, nodata = read_stack(stack_path)
    eps = 1e-10
    cv_vv = bands["std_vv"] / (np.abs(bands["mean_vv"]) + eps)
    cv_vh = bands["std_vh"] / (np.abs(bands["mean_vh"]) + eps)
    score = cv_vv + cv_vh
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata) & (bands["mean_vh"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "temporal_cv")


def run_temporal_mad(stack_path, output_dir, config, tile_id):
    bands, profile, transform, nodata = read_stack(stack_path)
    mad_vv = np.abs(bands["mean_vv"] - bands["median_vv"])
    mad_vh = np.abs(bands["mean_vh"] - bands["median_vh"])
    score = mad_vv + mad_vh
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "temporal_mad")


def run_seasonal_difference(stack_path, output_dir, config, tile_id):
    """Approximate seasonal difference using mean vs median as proxy for dry/wet split."""
    bands, profile, transform, nodata = read_stack(stack_path)
    score = np.abs(bands["mean_vv"] - bands["median_vv"]) + np.abs(bands["mean_vh"] - bands["median_vh"])
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "seasonal_difference")


def run_crosspol_ratio(stack_path, output_dir, config, tile_id):
    bands, profile, transform, nodata = read_stack(stack_path)
    eps = 1e-10
    ratio = bands["mean_vh"] / (bands["mean_vv"] + eps)
    from scipy.ndimage import median_filter
    local_med = median_filter(ratio, size=21)
    score = np.abs(ratio - local_med)
    valid = np.isfinite(score) & (score > 0) & np.isfinite(ratio)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "crosspol_ratio")


def run_crosspol_ratio_variance(stack_path, output_dir, config, tile_id):
    bands, profile, transform, nodata = read_stack(stack_path)
    eps = 1e-10
    ratio_mean = bands["mean_vh"] / (bands["mean_vv"] + eps)
    ratio_var = bands["var_vh"] / ((bands["mean_vv"] + eps) ** 2)
    score = ratio_var
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "crosspol_ratio_variance")


def run_edge_detection(stack_path, output_dir, config, tile_id):
    bands, profile, transform, nodata = read_stack(stack_path)
    from scipy.ndimage import sobel
    sx_vv = sobel(bands["mean_vv"], axis=0)
    sy_vv = sobel(bands["mean_vv"], axis=1)
    sx_vh = sobel(bands["mean_vh"], axis=0)
    sy_vh = sobel(bands["mean_vh"], axis=1)
    score = np.sqrt(sx_vv**2 + sy_vv**2) + np.sqrt(sx_vh**2 + sy_vh**2)
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "edge_detection")


def run_spatial_autocorrelation(stack_path, output_dir, config, tile_id):
    """Local Moran's I approximation using z-score of local deviation."""
    bands, profile, transform, nodata = read_stack(stack_path)
    from scipy.ndimage import uniform_filter
    radius = config.get("config", {}).get("window_radius_px", 25)
    win = 2 * radius + 1
    local_mean = uniform_filter(bands["mean_vv"], size=win)
    local_var = uniform_filter(bands["mean_vv"]**2, size=win) - local_mean**2
    local_var = np.maximum(local_var, 1e-10)
    z = (bands["mean_vv"] - local_mean) / np.sqrt(local_var)
    score = np.abs(z)
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "spatial_autocorrelation")


def run_multitemporal_change(stack_path, output_dir, config, tile_id):
    """Proxy: use range = max - min ~ var_VV scaled. With only stack stats, use std as proxy."""
    bands, profile, transform, nodata = read_stack(stack_path)
    score = bands["std_vv"] * 2 + bands["std_vh"] * 2
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "multitemporal_change")


def run_texture_glcm(stack_path, output_dir, config, tile_id):
    """Simplified texture: use local standard deviation as proxy for GLCM contrast."""
    bands, profile, transform, nodata = read_stack(stack_path)
    from scipy.ndimage import generic_filter
    win = config.get("config", {}).get("window_size", 21)
    local_std = generic_filter(bands["mean_vv"], np.std, size=win)
    score = local_std
    valid = np.isfinite(score) & (score > 0)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "texture_glcm")


def run_backscatter_intensity(stack_path, output_dir, config, tile_id):
    os.makedirs(output_dir, exist_ok=True)
    with rasterio.open(stack_path) as src:
        profile = src.profile.copy()
        profile.update(count=2)
        with rasterio.open(os.path.join(output_dir, "intensity_map.tif"), "w", **profile) as dst:
            dst.write(src.read(1), 1)
            dst.write(src.read(2), 2)
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump({"scan_type": "backscatter_intensity", "tile_id": tile_id,
                    "num_candidates": 0, "candidate_count": 0,
                    "run_time_utc": datetime.utcnow().isoformat() + "Z"}, f, indent=2)
    print(f"  backscatter_intensity: baseline map written")
    return 0


# ---------- NEW SCAN TYPES (v3.1) ----------


def run_speckle_divergence(stack_path, output_dir, config, tile_id):
    """
    Speckle Divergence Index: separates real physical change from SAR speckle noise.
    For N-look GRD data, expected speckle variance = mean^2 / ENL.
    SDI = observed_variance / expected_speckle_variance.
    SDI >> 1 means real change; SDI ~ 1 means just speckle.
    """
    bands, profile, transform, nodata = read_stack(stack_path)
    num_images = config.get("config", {}).get("num_images", 12)
    eps = 1e-20
    expected_var_vv = (bands["mean_vv"] ** 2) / max(num_images, 1) + eps
    expected_var_vh = (bands["mean_vh"] ** 2) / max(num_images, 1) + eps
    sdi_vv = bands["var_vv"] / expected_var_vv
    sdi_vh = bands["var_vh"] / expected_var_vh
    score = sdi_vv + sdi_vh
    valid = np.isfinite(score) & (score > 0) & (bands["mean_vv"] > eps)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 99)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "speckle_divergence")


def run_db_variance(stack_path, output_dir, config, tile_id):
    """
    dB-domain variance: convert mean and variance to decibel scale before scoring.
    In dB, the distribution is more Gaussian and subtle features become prominent.
    Uses delta method: var_dB ≈ (10/ln10)^2 * var_linear / mean_linear^2
    """
    bands, profile, transform, nodata = read_stack(stack_path)
    eps = 1e-20
    k = (10.0 / np.log(10.0)) ** 2
    var_db_vv = k * bands["var_vv"] / (bands["mean_vv"] ** 2 + eps)
    var_db_vh = k * bands["var_vh"] / (bands["mean_vh"] ** 2 + eps)
    score = var_db_vv + var_db_vh
    valid = np.isfinite(score) & (score > 0) & (bands["mean_vv"] > eps)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 99)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "db_variance")


def run_moisture_differential(stack_path, output_dir, config, tile_id):
    """
    Soil Moisture Differential: VV is sensitive to soil moisture + structure;
    VH is sensitive to volume scattering (vegetation, roughness).
    Where VV temporal variance is high but VH is stable, the signal likely comes
    from dielectric anomalies (buried walls/foundations retaining moisture differently).
    Score = var_VV / (var_VH + eps) — high means VV-only change.
    """
    bands, profile, transform, nodata = read_stack(stack_path)
    eps = 1e-20
    ratio = bands["var_vv"] / (bands["var_vh"] + eps)
    score = np.abs(np.log10(ratio + eps))
    valid = np.isfinite(score) & (score > 0) & (bands["var_vh"] > eps)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "moisture_differential")


def run_depolarization_fraction(stack_path, output_dir, config, tile_id):
    """
    Depolarization Fraction: VH / (VV + VH).
    Measures what fraction of energy is depolarized by the surface.
    Buried structures cause double-bounce scattering → different depol fraction
    than flat desert (single-bounce). Anomaly = deviation from local median.
    """
    bands, profile, transform, nodata = read_stack(stack_path)
    eps = 1e-20
    depol = bands["mean_vh"] / (bands["mean_vv"] + bands["mean_vh"] + eps)
    from scipy.ndimage import median_filter
    local_med = median_filter(depol, size=31)
    score = np.abs(depol - local_med)
    valid = np.isfinite(score) & (score > 0) & np.isfinite(depol)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "depolarization_fraction")


def run_local_contrast(stack_path, output_dir, config, tile_id):
    """
    Local Contrast Ratio: pixel / local_mean.
    Highlights features that stand out against their neighborhood regardless
    of overall scene brightness. Values far from 1.0 = anomalous.
    """
    bands, profile, transform, nodata = read_stack(stack_path)
    from scipy.ndimage import uniform_filter
    win = config.get("config", {}).get("window_size", 31)
    local_mean_vv = uniform_filter(bands["mean_vv"], size=win)
    local_mean_vh = uniform_filter(bands["mean_vh"], size=win)
    eps = 1e-20
    contrast_vv = np.abs(np.log(bands["mean_vv"] / (local_mean_vv + eps) + eps))
    contrast_vh = np.abs(np.log(bands["mean_vh"] / (local_mean_vh + eps) + eps))
    score = contrast_vv + contrast_vh
    valid = np.isfinite(score) & (score > 0) & (local_mean_vv > eps)
    if nodata is not None:
        valid &= (bands["mean_vv"] != nodata)
    pct = config.get("threshold_percentile", 95)
    return threshold_and_output(score, valid, pct, output_dir, profile, transform, tile_id, "local_contrast")


def run_hotspot_cluster(stack_path, output_dir, config, tile_id):
    """
    Candidate Hotspot Clustering: load candidates from all other scan types
    for this tile, cluster with DBSCAN. Locations where >=N scan types agree
    within a radius are high-confidence.
    """
    os.makedirs(output_dir, exist_ok=True)
    tile_dir = os.path.dirname(output_dir)
    import glob

    all_coords = []
    all_scan_types = []
    for gj_path in sorted(glob.glob(os.path.join(tile_dir, "*", "candidates.geojson"))):
        st_name = os.path.basename(os.path.dirname(gj_path))
        if st_name == "hotspot_cluster":
            continue
        try:
            with open(gj_path) as f:
                fc = json.load(f)
            for feat in fc.get("features", []):
                c = feat["geometry"]["coordinates"]
                all_coords.append((c[0], c[1]))
                all_scan_types.append(st_name)
        except Exception:
            continue

    if not all_coords:
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump({"scan_type": "hotspot_cluster", "tile_id": tile_id,
                        "num_candidates": 0, "candidate_count": 0,
                        "min_agreeing_types": config.get("config", {}).get("min_agreeing_types", 3),
                        "run_time_utc": datetime.utcnow().isoformat() + "Z"}, f, indent=2)
        return 0

    coords_arr = np.array(all_coords)
    scan_arr = np.array(all_scan_types)
    min_agree = config.get("config", {}).get("min_agreeing_types", 3)
    radius_deg = config.get("config", {}).get("radius_deg", 0.001)

    try:
        from sklearn.cluster import DBSCAN
    except ImportError:
        from scipy.spatial import cKDTree
        tree = cKDTree(coords_arr)
        groups = tree.query_ball_tree(tree, r=radius_deg)
        hotspots = []
        seen = set()
        for i, group in enumerate(groups):
            types_in_group = set(scan_arr[g] for g in group)
            if len(types_in_group) >= min_agree and i not in seen:
                center_lon = float(np.mean(coords_arr[group, 0]))
                center_lat = float(np.mean(coords_arr[group, 1]))
                hotspots.append({
                    "lon": center_lon, "lat": center_lat,
                    "agreeing_types": len(types_in_group),
                    "types": sorted(types_in_group),
                    "n_candidates": len(group),
                })
                seen.update(group)
    else:
        db = DBSCAN(eps=radius_deg, min_samples=min_agree, metric="euclidean")
        labels = db.fit_predict(coords_arr)
        hotspots = []
        for lab in set(labels):
            if lab == -1:
                continue
            mask = labels == lab
            types_in_cluster = set(scan_arr[mask])
            if len(types_in_cluster) >= min_agree:
                center_lon = float(np.mean(coords_arr[mask, 0]))
                center_lat = float(np.mean(coords_arr[mask, 1]))
                hotspots.append({
                    "lon": center_lon, "lat": center_lat,
                    "agreeing_types": len(types_in_cluster),
                    "types": sorted(types_in_cluster),
                    "n_candidates": int(mask.sum()),
                })

    hotspots.sort(key=lambda h: -h["agreeing_types"])

    features = []
    for h in hotspots:
        score = h["agreeing_types"] / max(len(set(all_scan_types)), 1)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [h["lon"], h["lat"]]},
            "properties": {
                "lon": h["lon"], "lat": h["lat"],
                "score": score, "chance": score,
                "agreeing_types": h["agreeing_types"],
                "types": h["types"],
                "n_candidates": h["n_candidates"],
                "tile_id": tile_id, "pathway": "hotspot_cluster",
            },
        })

    with open(os.path.join(output_dir, "candidates.geojson"), "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

    with open(os.path.join(output_dir, "candidates.csv"), "w") as f:
        f.write("lon,lat,agreeing_types,types,n_candidates,score,tile_id\n")
        for h in hotspots:
            f.write(f"{h['lon']},{h['lat']},{h['agreeing_types']},\"{';'.join(h['types'])}\",{h['n_candidates']},{h['agreeing_types']},{tile_id}\n")

    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump({
            "scan_type": "hotspot_cluster", "tile_id": tile_id,
            "num_candidates": len(hotspots), "candidate_count": len(hotspots),
            "min_agreeing_types": min_agree, "radius_deg": radius_deg,
            "input_candidates": len(all_coords),
            "input_scan_types": sorted(set(all_scan_types)),
            "run_time_utc": datetime.utcnow().isoformat() + "Z",
        }, f, indent=2)

    print(f"  hotspot_cluster: {len(hotspots)} hotspots (from {len(all_coords)} candidates across {len(set(all_scan_types))} types)")
    return len(hotspots)


RUNNERS = {
    "temporal_variance": run_temporal_variance,
    "temporal_cv": run_temporal_cv,
    "temporal_mad": run_temporal_mad,
    "seasonal_difference": run_seasonal_difference,
    "crosspol_ratio": run_crosspol_ratio,
    "crosspol_ratio_variance": run_crosspol_ratio_variance,
    "edge_detection": run_edge_detection,
    "spatial_autocorrelation": run_spatial_autocorrelation,
    "multitemporal_change": run_multitemporal_change,
    "texture_glcm": run_texture_glcm,
    "backscatter_intensity": run_backscatter_intensity,
    "speckle_divergence": run_speckle_divergence,
    "db_variance": run_db_variance,
    "moisture_differential": run_moisture_differential,
    "depolarization_fraction": run_depolarization_fraction,
    "local_contrast": run_local_contrast,
    "hotspot_cluster": run_hotspot_cluster,
}


def main():
    if len(sys.argv) < 4:
        print("Usage: run_scan_type.py <stack_path> <scan_type_name> <output_dir> [tile_id]", file=sys.stderr)
        sys.exit(1)
    stack_path = sys.argv[1]
    scan_type_name = sys.argv[2]
    output_dir = sys.argv[3]
    tile_id = sys.argv[4] if len(sys.argv) > 4 else ""

    if rasterio is None:
        print("rasterio required", file=sys.stderr)
        sys.exit(1)

    scan_config = load_scan_config()
    scan_types = scan_config.get("scan_types", [])
    config = next((s for s in scan_types if s.get("name") == scan_type_name), None)
    if not config or not config.get("enabled", True):
        print(f"Scan type {scan_type_name} not found or disabled.", file=sys.stderr)
        sys.exit(1)

    # Match runner: exact name first, then prefix
    runner = RUNNERS.get(scan_type_name)
    if runner is None:
        for prefix, fn in RUNNERS.items():
            if scan_type_name.startswith(prefix):
                runner = fn
                break

    if runner is None:
        print(f"WARNING: No runner for {scan_type_name} — writing placeholder.", file=sys.stderr)
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump({"scan_type": scan_type_name, "tile_id": tile_id,
                        "num_candidates": 0, "candidate_count": 0,
                        "status": "not_implemented"}, f, indent=2)
        sys.exit(0)

    try:
        runner(stack_path, output_dir, config, tile_id)
    except Exception as e:
        print(f"ERROR in {scan_type_name}: {e}", file=sys.stderr)
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump({"scan_type": scan_type_name, "tile_id": tile_id,
                        "num_candidates": 0, "candidate_count": 0,
                        "status": "error", "error": str(e)}, f, indent=2)
        sys.exit(1)


if __name__ == "__main__":
    main()
