"""Extensions to interact with TaskGroups."""

import asyncio
from collections.abc import Coroutine
from contextlib import AbstractAsyncContextManager, suppress
from contextvars import Context
from types import TracebackType
from typing import Any, Never, Self, TypeVar

T = TypeVar("T")


class TerminateTaskGroup(BaseException):
    """Signal to terminate a task group.

    Technically not an exception, so inherits from `BaseException`.
    """


async def force_terminate_task_group() -> Never:
    """Force termination of a task group."""
    raise TerminateTaskGroup


class TaskGroup(AbstractAsyncContextManager["TaskGroup"]):
    """A version of asyncio.TaskGroup with a cancel method."""

    def __init__(self) -> None:  # noqa: D107
        self.tasks = asyncio.TaskGroup()

    async def __aenter__(self) -> Self:  # noqa: D105
        await self.tasks.__aenter__()
        return self

    async def __aexit__(  # noqa: D105
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        with suppress(TerminateTaskGroup):
            await self.tasks.__aexit__(exc_type, exc_value, traceback)
        return None

    def create_task(
        self,
        coro: Coroutine[Any, Any, T],
        *,
        name: str | None = None,
        context: Context | None = None,
    ) -> asyncio.Task[T]:
        """Create a new task in this group and return it."""
        return self.tasks.create_task(coro, name=name, context=context)

    def cancel(self) -> None:
        """Cancel any remaining task in the TaskGroup."""
        self.create_task(force_terminate_task_group())
