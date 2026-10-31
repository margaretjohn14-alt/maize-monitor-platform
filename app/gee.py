import ee
import os

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