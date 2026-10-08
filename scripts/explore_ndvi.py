"""Explore: mean NDVI over a small test area for one month.

Run with: python scripts/explore_ndvi.py
"""

import numpy as np
import odc.stac
import pystac_client

STAC_URL = "https://earth-search.aws.element84.com/v1"
# Small test area in north-western Free State, a major maize region (lon/lat)
BBOX = [26.3, -27.7, 27.0, -27.2]
MONTH = "2024-02"
# Scene classification classes kept: 4 = vegetation, 5 = bare soil
VALID_SCL = [4, 5]


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

    # Since January 2022 (processing baseline 04.00) reflectance has an offset of -0.1.
    # Check whether this archive already removed it before trusting NDVI values.
    baselines = {i.properties.get("s2:processing_baseline") for i in items}
    offset_applied = {i.properties.get("earthsearch:boa_offset_applied") for i in items}
    print(f"processing baselines: {baselines}")
    print(f"offset already applied: {offset_applied}")
    needs_offset = min(baselines) >= "04.00" and offset_applied == {False}
    offset = -0.1 if needs_offset else 0.0
    print(f"offset used: {offset}")

    data = odc.stac.load(
        items,
        bands=["red", "nir", "scl"],
        bbox=BBOX,
        crs="EPSG:32735",
        resolution=100,
        groupby="solar_day",
        chunks={},
    )
    valid = data.scl.isin(VALID_SCL)
    red = data.red.where(valid) * 0.0001 + offset
    nir = data.nir.where(valid) * 0.0001 + offset
    ndvi = (nir - red) / (nir + red)
    composite = ndvi.median(dim="time").compute()

    print(f"dates used: {[str(t)[:10] for t in data.time.values]}")
    print(f"mean NDVI: {float(composite.mean()):.3f}")
    print(f"valid pixels: {int(np.isfinite(composite).sum())} of {composite.size}")


if __name__ == "__main__":
    main()