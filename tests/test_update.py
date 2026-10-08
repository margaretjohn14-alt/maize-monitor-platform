from app.update import run


def test_update_processes_all_regions():
    assert run() == 2