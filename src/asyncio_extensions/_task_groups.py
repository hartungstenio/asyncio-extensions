"""Extensions to :mod:`asyncio` task groups."""

import asyncio
from collections.abc import Coroutine
from types import TracebackType
from typing import Any, Never, TypeVar, Unpack

from ._compat import CreateTaskParams, override

T = TypeVar("T")


class TerminateTaskGroup(BaseException):
    """Signal raised to terminate a :class:`TaskGroup` early.

    Inherits from :exc:`BaseException` to bypass normal exception handling
    inside the group. Raised by :func:`force_terminate_task_group` and
    suppressed by :meth:`TaskGroup.__aexit__`.
    """


async def force_terminate_task_group() -> Never:
    """Raise :exc:`TerminateTaskGroup` to stop the enclosing task group."""
    raise TerminateTaskGroup


class TaskGroup(asyncio.TaskGroup):
    """An :class:`asyncio.TaskGroup` extended with a :meth:`cancel` method."""

    async def __aexit__(
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
        """Schedule cancellation of all remaining tasks in the group."""
        self.create_task(force_terminate_task_group())


class LimitedTaskGroup(TaskGroup):
    """A :class:`TaskGroup` that caps the number of tasks running concurrently.

    Args:
        max_concurrent: Maximum number of tasks allowed to run at the same time.
    """

    def __init__(self, max_concurrent: int) -> None:
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
        """Schedule *coro* as a task, subject to the concurrency limit.

        Args:
            coro: The coroutine to run as a task.

        Returns:
            The created :class:`asyncio.Task`.
        """
        return super().create_task(self._task_wrapper(coro), **kwargs)
