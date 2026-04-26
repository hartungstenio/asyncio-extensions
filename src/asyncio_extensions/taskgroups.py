"""Extensions to interact with TaskGroups."""

import asyncio
from collections.abc import Coroutine
from types import TracebackType
from typing import Any, Never, TypeVar, Unpack

from ._compat import CreateTaskParams, override

T = TypeVar("T")


class TerminateTaskGroup(BaseException):
    """Signal to terminate a task group.

    Technically not an exception, so inherits from `BaseException`.
    """


async def force_terminate_task_group() -> Never:
    """Force termination of a task group."""
    raise TerminateTaskGroup


class TaskGroup(asyncio.TaskGroup):
    """A version of asyncio.TaskGroup with a cancel method."""

    async def __aexit__(  # noqa: D105
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc_value, traceback)
        except* TerminateTaskGroup:
            pass

    def cancel(self) -> None:
        """Cancel any remaining task in the TaskGroup."""
        self.create_task(force_terminate_task_group())


class LimitedTaskGroup(TaskGroup):
    """A TaskGroup that limits the number of concurrent tasks."""

    def __init__(self, max_concurrent: int) -> None:
        """Initialize the LimitedTaskGroup.

        Args:
            max_concurrent: Maximum number of concurrent tasks.
        """
        super().__init__()
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _task_wrapper(self, coro: Coroutine[Any, Any, T]) -> T:
        async with self._semaphore:
            return await coro

    @override
    def create_task(
        self,
        coro: Coroutine[Any, Any, T],
        **kwargs: Unpack[CreateTaskParams],
    ) -> asyncio.Task[T]:
        """Create a task within the limited concurrency context.

        Args:
            coro: The coroutine to run as a task.

        Returns:
            The created asyncio Task.
        """
        return super().create_task(self._task_wrapper(coro), **kwargs)
