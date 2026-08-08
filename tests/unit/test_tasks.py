import pytest

from src.app.services.sample_service import compute_answer
from src.tasks.base import BaseTask, TaskConfig, is_retryable_error
from src.tasks.nightly_cleanup import NightlyCleanupTask
from src.tasks.sync_things import SyncThingsTask


async def test_nightly_cleanup_run():
    result = await NightlyCleanupTask().execute_safe()
    assert result.success is True
    assert result.data == "Nightly cleanup done (scope=all)"
    assert result.task_id == "nightly-cleanup"


async def test_sync_things_uses_event_params():
    config = TaskConfig(params={"region": "eu-west-1"})
    result = await SyncThingsTask().execute_safe(config)
    assert result.success is True
    assert result.data == "Sync completed (region=eu-west-1)"


async def test_sample_service_compute_answer():
    assert compute_answer(2, 3) == 5


class _FlakyTask(BaseTask):
    """Fails with a retryable error until the given attempt succeeds."""

    task_id = "flaky"

    def __init__(self, fail_times: int, error: Exception | None = None) -> None:
        self.fail_times = fail_times
        self.calls = 0
        self.error = error or RuntimeError("status_code: 503 upstream busy")

    async def run(self, config: TaskConfig) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.error
        return "ok"


_NO_WAIT = {"base_delay_seconds": 0.0, "max_delay_seconds": 0.0}


async def test_execute_safe_retries_transient_errors():
    task = _FlakyTask(fail_times=2)
    result = await task.execute_safe(TaskConfig(max_retries=3, **_NO_WAIT))

    assert result.success is True
    assert result.data == "ok"
    assert result.attempts == 3
    assert task.calls == 3


async def test_execute_safe_gives_up_after_max_retries():
    task = _FlakyTask(fail_times=99)
    result = await task.execute_safe(TaskConfig(max_retries=2, **_NO_WAIT))

    assert result.success is False
    assert result.attempts == 2
    assert "503" in (result.error or "")
    assert task.calls == 2


async def test_execute_safe_does_not_retry_permanent_errors():
    task = _FlakyTask(fail_times=99, error=ValueError("bad input"))
    result = await task.execute_safe(TaskConfig(max_retries=5, **_NO_WAIT))

    assert result.success is False
    assert result.attempts == 1
    assert task.calls == 1


async def test_execute_raises_the_original_error():
    task = _FlakyTask(fail_times=99, error=ValueError("bad input"))
    with pytest.raises(ValueError, match="bad input"):
        await task.execute(TaskConfig(max_retries=1, **_NO_WAIT))


async def test_execute_safe_reports_timing_and_date():
    result = await NightlyCleanupTask().execute_safe()
    assert result.execution_time_ms >= 0
    assert result.execution_date.endswith("+00:00")


def test_backoff_is_exponential_and_capped():
    task = NightlyCleanupTask()
    config = TaskConfig(base_delay_seconds=2, max_delay_seconds=5)
    assert task._delay_for(1, config) == 2
    assert task._delay_for(2, config) == 4
    assert task._delay_for(3, config) == 5  # capped


@pytest.mark.parametrize(
    "error,expected",
    [
        (RuntimeError("status_code: 429 too many requests"), True),
        (RuntimeError("HTTP status=502"), True),
        (RuntimeError("status_code: 400 bad request"), False),
        (RuntimeError("Connection reset by peer"), True),
        (TimeoutError("deadline"), True),
        (ValueError("nope"), False),
    ],
)
def test_is_retryable_error(error, expected):
    assert is_retryable_error(error) is expected
