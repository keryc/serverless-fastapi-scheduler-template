"""
Base Task

Abstract base class for scheduled tasks. Provides timing, retry with
exponential backoff on transient errors, and a structured result wrapper so a
failing task returns a value instead of killing the Lambda invocation.
"""

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# HTTP status codes that are safe to retry (transient errors)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504, 524}

# Substrings that indicate a transient failure worth retrying
RETRYABLE_MESSAGES = (
    "timeout",
    "timed out",
    "connection reset",
    "connection closed",
    "connection aborted",
    "temporarily unavailable",
)

# Default retry configuration. Keep the worst case (sum of the delays) well
# below the function timeout in serverless.yml.
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 2.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds


def is_retryable_error(error: Exception) -> bool:
    """Return True when the error looks transient and is worth retrying."""
    message = str(error)

    status_match = re.search(r"status(?:_code)?[\"']?\s*[:=]\s*(\d{3})", message, re.IGNORECASE)
    if status_match:
        return int(status_match.group(1)) in RETRYABLE_STATUS_CODES

    status_code = getattr(getattr(error, "response", None), "status_code", None)
    if isinstance(status_code, int):
        return status_code in RETRYABLE_STATUS_CODES

    if isinstance(error, TimeoutError | ConnectionError):
        return True

    lowered = message.lower()
    return any(keyword in lowered for keyword in RETRYABLE_MESSAGES)


class TaskExecutionError(Exception):
    """Internal wrapper carrying how many attempts were spent before failing.

    The original exception is always available as ``__cause__``.
    """

    def __init__(self, attempts: int) -> None:
        super().__init__(f"task failed after {attempts} attempt(s)")
        self.attempts = attempts


class TaskConfig(BaseModel):
    """Configuration for a single task execution.

    ``params`` carries whatever the EventBridge rule passed as ``input`` (see
    ``events/*.yml``), so one handler can serve many schedules.
    """

    model_config = ConfigDict(extra="forbid")

    params: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=DEFAULT_MAX_RETRIES, ge=1)
    base_delay_seconds: float = Field(default=DEFAULT_BASE_DELAY, ge=0)
    max_delay_seconds: float = Field(default=DEFAULT_MAX_DELAY, ge=0)


class TaskResult(BaseModel):
    """Structured outcome of a task execution."""

    task_id: str
    success: bool
    data: Any = None
    error: str | None = None
    attempts: int = 1
    execution_date: str
    execution_time_ms: int


class BaseTask(ABC):
    """Abstract base class for all scheduled tasks.

    Subclasses implement ``run``. ``task_id`` is set by the
    :func:`src.tasks.registry.register_task` decorator.
    """

    task_id: str
    #: Overridable per task; ``TaskConfig.max_retries`` wins when provided.
    max_retries: int = DEFAULT_MAX_RETRIES

    @abstractmethod
    async def run(self, config: TaskConfig) -> Any:
        """Do the actual work. Raise to signal failure."""
        ...

    def _delay_for(self, attempt: int, config: TaskConfig) -> float:
        """Exponential backoff delay for the given (1-based) attempt."""
        return float(
            min(config.base_delay_seconds * (2 ** (attempt - 1)), config.max_delay_seconds)
        )

    async def _run_with_retries(self, config: TaskConfig) -> tuple[Any, int]:
        """Run the task with retries, returning the result and attempts used."""
        max_retries = max(config.max_retries, 1)

        for attempt in range(1, max_retries + 1):
            try:
                return await self.run(config), attempt
            except Exception as error:
                if attempt >= max_retries or not is_retryable_error(error):
                    logger.error("Task %s failed on attempt %d: %s", self.task_id, attempt, error)
                    raise TaskExecutionError(attempt) from error
                delay = self._delay_for(attempt, config)
                logger.warning(
                    "Task %s attempt %d/%d failed (%s), retrying in %.1fs",
                    self.task_id,
                    attempt,
                    max_retries,
                    error,
                    delay,
                )
                await asyncio.sleep(delay)

        raise AssertionError("unreachable")  # pragma: no cover

    async def execute(self, config: TaskConfig | None = None) -> Any:
        """Run the task, retrying transient failures. Raises on final failure."""
        try:
            data, _ = await self._run_with_retries(config or TaskConfig())
        except TaskExecutionError as wrapper:
            raise wrapper.__cause__ from None  # type: ignore[misc]
        return data

    async def execute_safe(self, config: TaskConfig | None = None) -> TaskResult:
        """Run the task and wrap success or failure in a :class:`TaskResult`."""
        config = config or TaskConfig()
        started = time.monotonic()

        try:
            data, attempts = await self._run_with_retries(config)
        except TaskExecutionError as wrapper:
            return TaskResult(
                task_id=self.task_id,
                success=False,
                error=str(wrapper.__cause__),
                attempts=wrapper.attempts,
                execution_date=datetime.now(UTC).isoformat(),
                execution_time_ms=int((time.monotonic() - started) * 1000),
            )

        return TaskResult(
            task_id=self.task_id,
            success=True,
            data=data,
            attempts=attempts,
            execution_date=datetime.now(UTC).isoformat(),
            execution_time_ms=int((time.monotonic() - started) * 1000),
        )
