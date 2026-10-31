from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_regions_lists_ids_and_names():
    body = client.get("/regions").json()
    assert {"id": "free-state", "name": "Free State, South Africa"} in body


def test_estimate_returns_series_and_yield():
    with patch("app.main.fetch_ndvi", return_value=0.45):
        body = client.get("/estimate/free-state").json()
    assert len(body["ndvi_series"]) == 1
    assert body["ndvi_series"][0]["ndvi"] == 0.45
    assert body["yield_t_per_ha"] > 0
    assert body["data_source"] == "Sentinel-2 via Google Earth Engine"


def test_unknown_region_gives_404():
    assert client.get("/estimate/atlantis").status_code == 404


def test_version():
    assert client.get("/version").json() == {"version": "0.1.0"}