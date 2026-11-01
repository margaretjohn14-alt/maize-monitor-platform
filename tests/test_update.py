from unittest.mock import patch

from app.update import run


def test_update_processes_all_regions():
    with patch("app.update.fetch_ndvi", return_value=0.45):
        assert run() == 6