"""Explore: mean NDVI over a small test area for one month.

Run with: python scripts/explore_ndvi.py
"""

import numpy as np
import odc.stac
import pystac_client
import xarray as xr

STAC_URL = "https://earth-search.aws.element84.com/v1"
# Small test area in north-western Free State, a major maize region (lon/lat)
BBOX = [26.3, -27.7, 27.0, -27.2]
MONTH = "2024-02"
CRS = "EPSG:32735"
RESOLUTION = 100
# Scene classification classes kept: 4 = vegetation, 5 = bare soil
VALID_SCL = [4, 5]


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


def load_ndvi(items, offset: float) -> xr.DataArray:
    data = odc.stac.load(
        items,
        bands=["red", "nir", "scl"],
        bbox=BBOX,
        crs=CRS,
        resolution=RESOLUTION,
        groupby="solar_day",
        chunks={},
    )
    valid = data.scl.isin(VALID_SCL)
    red = data.red.where(valid) * 0.0001 + offset
    nir = data.nir.where(valid) * 0.0001 + offset
    return (nir - red) / (nir + red)


def main() -> None:
    catalog = pystac_client.Client.open(STAC_URL)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=BBOX,
        datetime=MONTH,
        query={"eo:cloud_cover": {"lt": 40}},
    )
    items = list(search.items())
    print(f"scenes found: {len(items)}")
    if not items:
        return

    items = deduplicate(items)
    print(f"scenes after removing duplicate versions: {len(items)}")
    print(f"processing baselines: {sorted({baseline(i) for i in items})}")

    with_offset = [i for i in items if needs_offset(i)]
    without_offset = [i for i in items if not needs_offset(i)]
    print(f"scenes corrected for offset: {len(with_offset)}, not corrected: {len(without_offset)}")

    parts = []
    if with_offset:
        parts.append(load_ndvi(with_offset, -0.1))
    if without_offset:
        parts.append(load_ndvi(without_offset, 0.0))
    ndvi = xr.concat(parts, dim="time")
    composite = ndvi.median(dim="time").compute()

    print(f"dates used: {sorted({str(t)[:10] for t in ndvi.time.values})}")
    print(f"mean NDVI: {float(composite.mean()):.3f}")
    print(f"valid pixels: {int(np.isfinite(composite).sum())} of {composite.size}")


if __name__ == "__main__":
    main()