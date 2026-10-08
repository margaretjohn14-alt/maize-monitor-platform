"""Monthly NDVI for every growing season in the reference statistics, then a comparison.

Run from the project folder with: python -m scripts.ndvi_timeseries

Finished months are saved as they complete. If the run stops, start it again:
months already in the output file are skipped.
"""

import csv
import logging
import time
from pathlib import Path

import numpy as np

REFERENCE = Path("data/reference/free_state_maize.csv")
OUTPUT = Path("data/ndvi/test_area_monthly.csv")
# Small test area in north-western Free State, a major maize region (lon/lat)
BBOX = [26.3, -27.7, 27.0, -27.2]
# Growing season months: November of the first year to April of the second
SEASON_MONTHS = [(0, 11), (0, 12), (1, 1), (1, 2), (1, 3), (1, 4)]
FIELDS = ["season", "month", "mean_ndvi", "clear_dates", "valid_fraction", "baselines", "status"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ndvi_timeseries")


def read_reference(path: Path = REFERENCE) -> dict:
    """Season -> official yield, final figures only."""
    with open(path, encoding="utf-8") as f:
        return {
            row["season"]: float(row["yield_t_ha"])
            for row in csv.DictReader(f)
            if row["status"] == "final"
        }


def season_months(season: str) -> list:
    """'2022/23' -> ['2022-11', '2022-12', '2023-01', '2023-02', '2023-03', '2023-04']"""
    start = int(season[:4])
    return [f"{start + offset}-{month:02d}" for offset, month in SEASON_MONTHS]


def done_months(path: Path = OUTPUT) -> set:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {row["month"] for row in csv.DictReader(f) if row["status"] == "ok"}


def append_row(row: dict, path: Path = OUTPUT) -> None:
    new_file = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def collect(seasons: list) -> None:
    from pipeline.sentinel import monthly_ndvi  # heavy imports only when downloading

    finished = done_months()
    for season in seasons:
        for month in season_months(season):
            if month in finished:
                log.info("skip %s (already done)", month)
                continue
            started = time.monotonic()
            try:
                result = monthly_ndvi(BBOX, month)
                status = "ok" if result["mean_ndvi"] is not None else "no_data"
            except Exception:
                # Catch everything on purpose: one failed month must not stop the whole batch.
                log.exception("month=%s failed", month)
                result = {"mean_ndvi": None, "clear_dates": 0, "valid_fraction": 0.0, "baselines": ""}
                status = "error"
            append_row({"season": season, "month": month, **result, "status": status})
            log.info(
                "month=%s status=%s ndvi=%s dates=%s seconds=%.0f",
                month, status, result["mean_ndvi"], result["clear_dates"],
                time.monotonic() - started,
            )


def summarize(reference: dict, path: Path = OUTPUT) -> list:
    """Per season: peak and sum of monthly NDVI, next to the official yield."""
    by_season = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["status"] == "ok":
                by_season.setdefault(row["season"], []).append(float(row["mean_ndvi"]))

    rows = []
    for season, values in sorted(by_season.items()):
        if season in reference and len(values) == len(SEASON_MONTHS):
            rows.append({
                "season": season,
                "yield": reference[season],
                "peak": max(values),
                "total": sum(values),
            })
    return rows


def correlation(rows: list, key: str) -> float:
    return float(np.corrcoef([r[key] for r in rows], [r["yield"] for r in rows])[0, 1])


def main() -> None:
    reference = read_reference()
    collect(sorted(reference))

    rows = summarize(reference)
    print(f"\n{'season':<9}{'yield t/ha':>11}{'peak NDVI':>11}{'sum NDVI':>10}")
    for r in rows:
        print(f"{r['season']:<9}{r['yield']:>11.2f}{r['peak']:>11.3f}{r['total']:>10.3f}")
    if len(rows) >= 3:
        print(f"\ncorrelation with yield: peak {correlation(rows, 'peak'):.2f}, "
              f"sum {correlation(rows, 'total'):.2f}  (seasons: {len(rows)})")
    else:
        print("\nToo few complete seasons for a correlation.")


if __name__ == "__main__":
    main()
