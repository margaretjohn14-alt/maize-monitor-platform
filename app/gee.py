import ee
import os

def init_ee():
    key = os.environ.get("GEE_SERVICE_ACCOUNT_KEY")
    if key:
        creds = ee.ServiceAccountCredentials(
            email="maize-monitor-platform@inbound-lattice-403009.iam.gserviceaccount.com",
            key_data=key,
        )
        ee.Initialize(creds)
    else:
        ee.Initialize()  # local dev with browser auth

init_ee()

def fetch_ndvi(bbox: list[float], start="2024-04-01", end="2024-09-30") -> float | None:
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