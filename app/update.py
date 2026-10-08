"""Weekly data update. Run with: python -m app.update"""

import logging

from app.core import estimate_yield, load_regions, season_ndvi

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("update")


def run() -> int:
    regions = load_regions()
    for region_id, region in regions.items():
        series = season_ndvi(region["observations"])
        model = region["model"]
        result = estimate_yield(series, model["slope"], model["intercept"])
        log.info("region=%s observations=%d yield_t_per_ha=%s", region_id, len(series), result)
    log.info("update finished, regions=%d", len(regions))
    return len(regions)


if __name__ == "__main__":
    run()