from typing import Any

from src.tasks.nightly_cleanup import run as nightly_run
from src.tasks.sync_things import run as sync_run


def nightly_handler_utc(event: dict[str, Any], context: Any) -> dict[str, Any]:
    result = nightly_run()
    return {"ok": True, "scheduler": "eventbridge-rule", "result": result}


def sync_handler_utc(event: dict[str, Any], context: Any) -> dict[str, Any]:
    result = sync_run()
    return {"ok": True, "scheduler": "eventbridge-rule", "result": result}
