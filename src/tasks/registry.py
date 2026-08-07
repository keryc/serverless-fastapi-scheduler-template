"""
Task Registry

Central registry of scheduled tasks. A task registers itself with the
``@register_task("...")`` decorator, so adding a task means adding a module,
not another Lambda handler.
"""

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.tasks.base import BaseTask

_TASK_REGISTRY: dict[str, type["BaseTask"]] = {}

_discovered = False


def register_task(task_id: str):
    """Decorator registering a task class under ``task_id``.

    Usage::

        @register_task("nightly-cleanup")
        class NightlyCleanupTask(BaseTask):
            ...
    """

    def decorator(cls: type["BaseTask"]) -> type["BaseTask"]:
        if task_id in _TASK_REGISTRY and _TASK_REGISTRY[task_id] is not cls:
            raise ValueError(f"Task id '{task_id}' is already registered")
        cls.task_id = task_id
        _TASK_REGISTRY[task_id] = cls
        return cls

    return decorator


class TaskRegistry:
    """Lookup helpers over the registered tasks."""

    @staticmethod
    def get(task_id: str) -> type["BaseTask"]:
        """Get a task class by id."""
        discover_tasks()
        if task_id not in _TASK_REGISTRY:
            raise ValueError(
                f"Task '{task_id}' not found. Available: {sorted(_TASK_REGISTRY.keys())}"
            )
        return _TASK_REGISTRY[task_id]

    @staticmethod
    def get_instance(task_id: str) -> "BaseTask":
        """Instantiate a task by id."""
        return TaskRegistry.get(task_id)()

    @staticmethod
    def exists(task_id: str) -> bool:
        """Whether a task id is registered."""
        discover_tasks()
        return task_id in _TASK_REGISTRY

    @staticmethod
    def all_ids() -> list[str]:
        """All registered task ids, sorted."""
        discover_tasks()
        return sorted(_TASK_REGISTRY)

    @staticmethod
    def list_all() -> list[dict]:
        """Metadata for every registered task."""
        discover_tasks()
        return [
            {"id": task_id, "max_retries": cls.max_retries}
            for task_id, cls in sorted(_TASK_REGISTRY.items())
        ]


def discover_tasks(force: bool = False) -> None:
    """Import every module under ``src.tasks`` to trigger registration.

    Idempotent: repeated calls are cheap no-ops.
    """
    global _discovered
    if _discovered and not force:
        return

    import src.tasks

    for module in pkgutil.iter_modules(src.tasks.__path__):
        if module.name in {"base", "registry"} or module.name.startswith("_"):
            continue
        importlib.import_module(f"src.tasks.{module.name}")

    _discovered = True
