from typing import Any

from src.tasks.base import BaseTask, TaskConfig
from src.tasks.registry import register_task


@register_task("nightly-cleanup")
class NightlyCleanupTask(BaseTask):
    """Example scheduled task. Keep the work idempotent: EventBridge delivers
    at-least-once and Lambda retries async invocations."""

    async def run(self, config: TaskConfig) -> Any:
        scope = config.params.get("scope", "all")
        return f"Nightly cleanup done (scope={scope})"
