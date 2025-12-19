import asyncio
from contextlib import AbstractAsyncContextManager, suppress
from typing import TYPE_CHECKING, Any, Never, Self, TypeVar

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from contextvars import Context
    from types import TracebackType

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

    def __init__(self) -> None:
        self.tasks = asyncio.TaskGroup()

    async def __aenter__(self) -> Self:
        await self.tasks.__aenter__()
        return self

    async def __aexit__(
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
        return self.tasks.create_task(coro, name=name, context=context)

    def cancel(self) -> None:
        self.create_task(force_terminate_task_group())
