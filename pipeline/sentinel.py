"""Sentinel-2 access and NDVI: shared by the exploration and time-series scripts."""

import numpy as np
import odc.stac
import pystac_client
import xarray as xr

STAC_URL = "https://earth-search.aws.element84.com/v1"
CRS = "EPSG:32735"
RESOLUTION = 100
# Scene classification classes kept: 4 = vegetation, 5 = bare soil
VALID_SCL = [4, 5]
MAX_CLOUD = 40


def baseline(item) -> str:
    return item.properties.get("s2:processing_baseline") or "00.00"


def needs_offset(item) -> bool:
    """Baseline 04.00 and later carry a -0.1 reflectance offset, unless the archive removed it."""
    applied = item.properties.get("earthsearch:boa_offset_applied")
    return baseline(item) >= "04.00" and applied is not True


def deduplicate(items) -> list:
    """Keep one version per tile and day: the most recent processing baseline."""
    best = {}
    for item in items:
        tile = item.properties.get("grid:code") or item.properties.get("s2:mgrs_tile") or item.id
        key = (tile, item.datetime.date())
        if key not in best or baseline(item) > baseline(best[key]):
            best[key] = item
    return list(best.values())


def search(bbox: list, month: str) -> list:
    catalog = pystac_client.Client.open(STAC_URL)
    found = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=month,
        query={"eo:cloud_cover": {"lt": MAX_CLOUD}},
    )
    return deduplicate(list(found.items()))


def load_ndvi(items, bbox: list, offset: float) -> xr.DataArray:
    data = odc.stac.load(
        items,
        bands=["red", "nir", "scl"],
        bbox=bbox,
        crs=CRS,
        resolution=RESOLUTION,
        groupby="solar_day",
        chunks={},
    )
    valid = data.scl.isin(VALID_SCL)
    red = data.red.where(valid) * 0.0001 + offset
    nir = data.nir.where(valid) * 0.0001 + offset
    return (nir - red) / (nir + red)


def monthly_ndvi(bbox: list, month: str) -> dict:
    """Median NDVI composite for one month, reduced to one mean value for the area."""
    items = search(bbox, month)
    if not items:
        return {"mean_ndvi": None, "clear_dates": 0, "valid_fraction": 0.0, "baselines": ""}

    parts = []
    with_offset = [i for i in items if needs_offset(i)]
    without_offset = [i for i in items if not needs_offset(i)]
    if with_offset:
        parts.append(load_ndvi(with_offset, bbox, -0.1))
    if without_offset:
        parts.append(load_ndvi(without_offset, bbox, 0.0))
    ndvi = xr.concat(parts, dim="time")
    composite = ndvi.median(dim="time").compute()

    return {
        "mean_ndvi": round(float(composite.mean()), 4),
        "clear_dates": len({str(t)[:10] for t in ndvi.time.values}),
        "valid_fraction": round(float(np.isfinite(composite).mean()), 4),
        "baselines": " ".join(sorted({baseline(i) for i in items})),
    }
