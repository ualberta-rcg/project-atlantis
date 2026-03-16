"""
Known and test sites: bbox (WGS84) and metadata for fetch/stack/detect pipeline.
bbox = [min_lon, min_lat, max_lon, max_lat]
"""
SITES = {
    # Known subsurface archaeology (Egypt), validated with Sentinel-1 in literature
    "qubbet_el_hawa": {
        "bbox": [32.85, 24.06, 32.93, 24.14],
        "name": "Qubbet el-Hawa (Aswan)",
        "description": "Rock-cut tombs, Old Kingdom; Sentinel-1 used for subsurface/radar-break studies.",
    },
    # Generic desert test (used earlier)
    "egypt_test": {
        "bbox": [29.9, 31.2, 30.1, 31.4],
        "name": "Egypt test tile",
        "description": "Small desert tile for pipeline test.",
    },
}

DEFAULT_TIME_WINDOWS = [
    ("2023-01-01", "2023-01-15"),
    ("2023-06-01", "2023-06-15"),
    ("2023-12-01", "2023-12-15"),
]
