#!/usr/bin/env python3
"""
Temporal variance scan type: var_VV + var_VH, threshold at configurable percentile.
Works on 4-band or 8-band stack (uses bands 3 and 4 for var_VV, var_VH).
"""
import os
import sys
import json

# Use existing detect_anomalies logic
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detect_anomalies import detect_anomalies


def run(stack_path, images_dir, output_dir, config, tile_id=""):
    """
    stack_path: path to stack.tif (mean_VV, mean_VH, var_VV, var_VH [, std, median...])
    images_dir: unused for this scan type
    output_dir: write anomaly.tif, candidates.geojson, candidates.csv, metadata.json
    config: scan type dict from scan.json (threshold_percentile, name, etc.)
    tile_id: for candidate properties
    """
    percentile = config.get("threshold_percentile", 95)
    scan_type_name = config.get("name", "temporal_variance_95")
    os.makedirs(output_dir, exist_ok=True)
    n, thresh = detect_anomalies(
        stack_path,
        output_dir,
        score_band="variance",
        percentile_threshold=percentile,
        site_id=tile_id,
        pathway=scan_type_name,
    )
    return n
