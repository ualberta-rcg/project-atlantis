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
    "hawara_labyrinth": {
        "bbox": [30.874, 29.247, 30.926, 29.293],
        "name": "Hawara Labyrinth (Faiyum)",
        "description": "Rumored site of the Egyptian Labyrinth described by Herodotus. Near Pyramid of Amenemhat III at Hawara, Faiyum.",
    },
    # Tanis (San el-Hagar) -- capital of Egypt during 21st-22nd Dynasties
    # 5km tile: center ~31.878E, 30.978N
    "tanis": {
        "bbox": [31.850, 30.955, 31.905, 31.000],
        "name": "Tanis (San el-Hagar)",
        "description": "Royal tombs, temples of Amun. Vast unexcavated areas. Sarah Parcak identified buried structures via satellite.",
    },
    # Ubar / Shisr -- 'Atlantis of the Sands', discovered via radar imagery
    # 5km tile: center ~54.633E, 18.255N
    "ubar": {
        "bbox": [54.605, 18.230, 54.660, 18.280],
        "name": "Ubar (Shisr, Oman)",
        "description": "Ancient frankincense trading post. Discovered 1992 using Shuttle Imaging Radar. Collapsed sinkhole over limestone cavern.",
    },
}

DEFAULT_TIME_WINDOWS = [
    ("2023-01-01", "2023-01-15"),
    ("2023-06-01", "2023-06-15"),
    ("2023-12-01", "2023-12-15"),
]
