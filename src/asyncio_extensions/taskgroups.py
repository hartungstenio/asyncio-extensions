"""Extensions to interact with TaskGroups."""

import asyncio
from types import TracebackType
from typing import Never, TypeVar

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
        try:  # noqa: SIM105
            await super().__aexit__(exc_type, exc_value, traceback)
        except* TerminateTaskGroup:
            pass

    def cancel(self) -> None:
        """Cancel any remaining task in the TaskGroup."""
        self.create_task(force_terminate_task_group())
