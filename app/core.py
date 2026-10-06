"""Science core: NDVI and a deliberately simple yield estimate.

Phase 1 replaces the sample data and the estimate with real inputs.
Keep this module free of web code so it can be tested on its own.
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "sample_regions.json"


def ndvi(red: float, nir: float) -> float:
    """Normalized Difference Vegetation Index from red and near-infrared reflectance."""
    total = nir + red
    if total == 0:
        return 0.0
    return (nir - red) / total


def load_regions(path: Path = DATA_FILE) -> dict:
    """Read the region file. Returns a dict keyed by region id."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def season_ndvi(observations: list[dict]) -> list[dict]:
    """Turn raw red/nir observations into an NDVI time series."""
    return [
        {"date": o["date"], "ndvi": round(ndvi(o["red"], o["nir"]), 3)}
        for o in observations
    ]


def estimate_yield(series: list[dict], slope: float, intercept: float) -> float:
    """Linear yield estimate (t/ha) from the season's peak NDVI.

    This is a placeholder model. The slope and intercept in the sample file
    are NOT fitted to real statistics. Fit them in phase 1.
    """
    if not series:
        raise ValueError("no observations for this region")
    peak = max(p["ndvi"] for p in series)
    return round(max(0.0, slope * peak + intercept), 2)
