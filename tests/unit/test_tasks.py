from src.app.services.sample_service import compute_answer
from src.tasks.nightly_cleanup import run as nightly_run
from src.tasks.sync_things import run as sync_run


def test_nightly_cleanup_run():
    assert nightly_run() == "Nightly cleanup done"


def test_sync_things_run():
    assert sync_run() == "Sync completed"


def test_sample_service_compute_answer():
    assert compute_answer(2, 3) == 5
