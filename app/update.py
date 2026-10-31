"""Weekly data update. Run with: python -m app.update"""

import logging

from app.core import estimate_yield, load_regions
from app.gee import fetch_ndvi

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("update")


def run() -> int:
    regions = load_regions()
    for region_id, region in regions.items():
        ndvi = fetch_ndvi(
            bbox=region["bbox"],
            start=region["season_start"],
            end=region["season_end"],
        )
        if ndvi is None:
            log.warning("region=%s no GEE data returned, skipping", region_id)
            continue
        series = [{"date": region["season"], "ndvi": round(ndvi, 4)}]
        model = region["model"]
        result = estimate_yield(series, model["slope"], model["intercept"])
        log.info("region=%s ndvi=%.4f yield_t_per_ha=%s", region_id, ndvi, result)
    log.info("update finished, regions=%d", len(regions))
    return len(regions)


if __name__ == "__main__":
    run()