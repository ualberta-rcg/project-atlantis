#!/usr/bin/env python3
"""
Run a single scan type on an existing stack. Used by run_pipeline after build_stack.
Usage: run_scan_type.py <stack_path> <scan_type_name> <output_dir> [tile_id]
"""
import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
SCAN_CONFIG_PATH = os.path.join(CONFIG_DIR, "scan.json")


def load_scan_config():
    if not os.path.isfile(SCAN_CONFIG_PATH):
        return {}
    with open(SCAN_CONFIG_PATH) as f:
        return json.load(f)


def main():
    if len(sys.argv) < 4:
        print("Usage: run_scan_type.py <stack_path> <scan_type_name> <output_dir> [tile_id]", file=sys.stderr)
        sys.exit(1)
    stack_path = sys.argv[1]
    scan_type_name = sys.argv[2]
    output_dir = sys.argv[3]
    tile_id = sys.argv[4] if len(sys.argv) > 4 else ""

    scan_config = load_scan_config()
    scan_types = scan_config.get("scan_types", [])
    config = next((s for s in scan_types if s.get("name") == scan_type_name), None)
    if not config or not config.get("enabled", True):
        print(f"Scan type {scan_type_name} not found or disabled.", file=sys.stderr)
        sys.exit(1)

    # Dispatch to scan_types/<name>.py
    if scan_type_name.startswith("temporal_variance"):
        from scan_types.temporal_variance import run
        run(stack_path, None, output_dir, config, tile_id=tile_id)
    elif scan_type_name == "backscatter_intensity":
        os.makedirs(output_dir, exist_ok=True)
        try:
            import rasterio
            with rasterio.open(stack_path) as src:
                profile = src.profile.copy()
                profile.update(count=2)
                intensity_path = os.path.join(output_dir, "intensity_map.tif")
                with rasterio.open(intensity_path, "w", **profile) as dst:
                    dst.write(src.read(1), 1)
                    dst.write(src.read(2), 2)
                with open(os.path.join(output_dir, "metadata.json"), "w") as f:
                    json.dump({"scan_type": scan_type_name, "tile_id": tile_id, "num_candidates": 0, "candidate_count": 0}, f, indent=2)
        except Exception as e:
            print(f"backscatter_intensity: {e}", file=sys.stderr)
    else:
        print(f"No runner for scan type {scan_type_name}. Add to run_scan_type.py.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
