"""
Task Lambda Handler

One generic handler for every scheduled task. ``TASK_ID`` comes from the
function's environment (serverless.yml); the per-schedule parameters come from
the EventBridge rule ``input`` (events/*.yml).
"""

import asyncio
import logging
import os
from typing import Any

from src.app.core.logging import configure_logging
from src.tasks.base import TaskConfig
from src.tasks.registry import TaskRegistry, discover_tasks

configure_logging()
discover_tasks()

logger = logging.getLogger(__name__)

# Event keys consumed by the handler itself rather than passed to the task.
_RESERVED_EVENT_KEYS = {"task_id"}


def task_handler(event: dict[str, Any] | None, context: Any) -> dict[str, Any]:
    """Execute the task named by ``TASK_ID`` (or ``event['task_id']``).

    Always returns a dict: task failures are reported as ``ok: False`` rather
    than raised, so Lambda's async retry + DLQ only trigger on real crashes.
    """
    event = event or {}
    task_id = event.get("task_id") or os.getenv("TASK_ID")

    if not task_id:
        logger.error("No task id: set the TASK_ID env var or pass task_id in the event")
        return {"ok": False, "error": "TASK_ID is not set"}

    params = {k: v for k, v in event.items() if k not in _RESERVED_EVENT_KEYS}

    try:
        task = TaskRegistry.get_instance(task_id)
    except ValueError as error:
        logger.error("Unknown task '%s': %s", task_id, error)
        return {"ok": False, "task_id": task_id, "error": str(error)}

    result = asyncio.run(task.execute_safe(TaskConfig(params=params)))

    return {
        "ok": result.success,
        "scheduler": "eventbridge-rule",
        **result.model_dump(),
    }
