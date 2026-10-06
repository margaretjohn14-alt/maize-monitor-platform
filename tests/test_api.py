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
    body = client.get("/estimate/free-state").json()
    assert len(body["ndvi_series"]) == 6
    assert body["yield_t_per_ha"] > 0


def test_unknown_region_gives_404():
    assert client.get("/estimate/atlantis").status_code == 404
