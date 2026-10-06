import pytest

from app.core import estimate_yield, load_regions, ndvi, season_ndvi


def test_ndvi_healthy_vegetation():
    assert ndvi(red=0.05, nir=0.45) == pytest.approx(0.8)


def test_ndvi_zero_input_does_not_crash():
    assert ndvi(0, 0) == 0.0


def test_season_ndvi_keeps_dates_and_order():
    series = season_ndvi([
        {"date": "2001-01-15", "red": 0.1, "nir": 0.3},
        {"date": "2001-02-15", "red": 0.05, "nir": 0.45},
    ])
    assert [p["date"] for p in series] == ["2001-01-15", "2001-02-15"]
    assert series[1]["ndvi"] == 0.8


def test_estimate_uses_peak_ndvi():
    series = [{"date": "a", "ndvi": 0.4}, {"date": "b", "ndvi": 0.8}]
    assert estimate_yield(series, slope=8.0, intercept=-1.0) == 5.4


def test_estimate_never_negative():
    series = [{"date": "a", "ndvi": 0.05}]
    assert estimate_yield(series, slope=8.0, intercept=-1.0) == 0.0


def test_estimate_rejects_empty_series():
    with pytest.raises(ValueError):
        estimate_yield([], slope=8.0, intercept=-1.0)


def test_sample_file_loads():
    assert "free-state" in load_regions()
