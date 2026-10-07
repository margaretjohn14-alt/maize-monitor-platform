"""Web API. Run locally with: uvicorn app.main:app --reload"""

from fastapi import FastAPI, HTTPException

from app.core import estimate_yield, load_regions, season_ndvi

app = FastAPI(title="Maize Monitor", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Used later by Docker and Kubernetes to check the service is alive."""
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
    series = season_ndvi(region["observations"])
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
