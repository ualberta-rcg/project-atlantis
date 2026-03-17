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
    # Hawara Labyrinth -- Herodotus' Egyptian Maze, near Pyramid of Amenemhat III
    # 5x5 km tile centered on ~30.899E, 29.274N (Hawara pyramid complex)
    "hawara_labyrinth": {
        "bbox": [30.874, 29.247, 30.926, 29.293],
        "name": "Hawara Labyrinth (Faiyum)",
        "description": "Rumored site of the Egyptian Labyrinth described by Herodotus. Near Pyramid of Amenemhat III at Hawara, Faiyum.",
    },
}

DEFAULT_TIME_WINDOWS = [
    ("2023-01-01", "2023-01-15"),
    ("2023-06-01", "2023-06-15"),
    ("2023-12-01", "2023-12-15"),
]
