import os
from datetime import date, timedelta

import ee

_initialized = False

def _ensure_initialized():
    global _initialized
    if _initialized:
        return
    key = os.environ.get("GEE_SERVICE_ACCOUNT_KEY")
    if key:
        creds = ee.ServiceAccountCredentials(
            email="maize-monitor-platform@inbound-lattice-403009.iam.gserviceaccount.com",
            key_data=key,
        )
        ee.Initialize(creds)
    else:
        ee.Initialize()
    _initialized = True


def fetch_ndvi(bbox: list[float], start="2024-04-01", end="2024-09-30") -> float | None:
    _ensure_initialized()
    region = ee.Geometry.Rectangle(bbox)
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
    )
    result = col.median().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=300,
        bestEffort=True,
    ).getInfo()
    return result.get("NDVI")


def fetch_ndvi_timeseries(
    bbox: list[float], start: str, end: str
) -> list[dict]:
    """Return monthly mean NDVI values between start and end dates.

    Returns a list of dicts: [{"month": "2024-06", "ndvi": 0.45}, ...]
    Months with no cloud-free imagery are omitted.
    """
    _ensure_initialized()
    region = ee.Geometry.Rectangle(bbox)

    # Build list of (month_start, month_end) pairs
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    months = []
    cur = date(s.year, s.month, 1)
    while cur <= e:
        next_month = date(cur.year + (cur.month // 12), (cur.month % 12) + 1, 1)
        m_end = min(next_month - timedelta(days=1), e)
        months.append((cur.isoformat(), m_end.isoformat()))
        cur = next_month

    results = []
    for m_start, m_end in months:
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(m_start, m_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
        )
        info = col.median().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=300,
            bestEffort=True,
        ).getInfo()
        ndvi = info.get("NDVI")
        if ndvi is not None:
            label = m_start[:7]  # "YYYY-MM"
            results.append({"month": label, "ndvi": round(ndvi, 4)})
    return results