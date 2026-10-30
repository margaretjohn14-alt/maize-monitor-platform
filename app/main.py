"""Web API. Run locally with: uvicorn app.main:app --reload"""

from fastapi import FastAPI, HTTPException
from app.core import estimate_yield, load_regions
from app.gee import fetch_ndvi

app = FastAPI(title="Maize Monitor", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/regions")
def regions() -> list[dict]:
    data = load_regions()
    return [{"id": key, "name": value["name"]} for key, value in data.items()]


@app.get("/estimate/{region_id}")
def estimate(region_id: str) -> dict:
    data = load_regions()
    if region_id not in data:
        raise HTTPException(status_code=404, detail=f"unknown region: {region_id}")
    region = data[region_id]

    ndvi_value = fetch_ndvi(
        bbox=region["bbox"],
        start=region["season_start"],
        end=region["season_end"],
    )

    if ndvi_value is None:
        raise HTTPException(status_code=503, detail="GEE returned no data for this region/season")

    series = [{"date": f"{region['season']}-mean", "ndvi": round(ndvi_value, 4)}]
    model = region["model"]

    return {
        "region": region_id,
        "name": region["name"],
        "season": region["season"],
        "ndvi_series": series,
        "yield_t_per_ha": estimate_yield(series, model["slope"], model["intercept"]),
        "data_source": region["source"],
    }


@app.get("/version")
def version() -> dict:
    return {"version": app.version}