import pytest

from src.tasks.base import BaseTask
from src.tasks.nightly_cleanup import NightlyCleanupTask
from src.tasks.registry import TaskRegistry, register_task


def test_example_tasks_are_discovered():
    assert "nightly-cleanup" in TaskRegistry.all_ids()
    assert "sync-things" in TaskRegistry.all_ids()


def test_get_returns_the_registered_class():
    assert TaskRegistry.get("nightly-cleanup") is NightlyCleanupTask


def test_get_instance_sets_task_id():
    task = TaskRegistry.get_instance("sync-things")
    assert isinstance(task, BaseTask)
    assert task.task_id == "sync-things"


def test_exists():
    assert TaskRegistry.exists("nightly-cleanup") is True
    assert TaskRegistry.exists("does-not-exist") is False


def test_get_unknown_task_lists_available_ids():
    with pytest.raises(ValueError, match="nightly-cleanup"):
        TaskRegistry.get("does-not-exist")


def test_list_all_includes_metadata():
    entries = {entry["id"]: entry for entry in TaskRegistry.list_all()}
    assert entries["nightly-cleanup"]["max_retries"] >= 1


def test_duplicate_registration_is_rejected():
    with pytest.raises(ValueError, match="already registered"):

        @register_task("nightly-cleanup")
        class Duplicate(BaseTask):
            async def run(self, config):
                return None
