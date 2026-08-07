from typing import Any

from src.tasks.base import BaseTask, TaskConfig
from src.tasks.registry import register_task


@register_task("sync-things")
class SyncThingsTask(BaseTask):
    """Example scheduled task showing per-schedule parameters.

    ``events/sync-things.yml`` defines one schedule per region; the region
    arrives in ``config.params`` so a single Lambda serves them all.
    """

    async def run(self, config: TaskConfig) -> Any:
        region = config.params.get("region", "global")
        return f"Sync completed (region={region})"
