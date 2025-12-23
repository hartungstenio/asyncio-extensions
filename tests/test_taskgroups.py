import asyncio

import pytest

from asyncio_extensions.taskgroups import (
    TaskGroup,
    TerminateTaskGroup,
    force_terminate_task_group,
)

from .utils import noop

pytestmark = pytest.mark.asyncio


async def test_force_terminate_task_group() -> None:
    with pytest.RaisesGroup(TerminateTaskGroup):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(asyncio.sleep(1000))
            tg.create_task(force_terminate_task_group())


class TestTaskGroup:
    async def test_runs_tasks(self) -> None:
        async with TaskGroup() as tg:
            tasks = [tg.create_task(noop()) for _ in range(10)]

        assert all(t.done() for t in tasks)
        assert not any(t.cancelled() for t in tasks)

    async def test_cancel_with_running_task(self) -> None:
        async with (
            asyncio.timeout(1),
            TaskGroup() as tg,
        ):
            task = tg.create_task(asyncio.sleep(10))
            tg.cancel()
        assert task.cancelled() is True

    async def test_cancel_without_running_task(self) -> None:
        async with TaskGroup() as tg:
            tg.cancel()

    async def test_cancel_with_done_task(self) -> None:
        async with (
            asyncio.timeout(1),
            TaskGroup() as tg,
        ):
            task = tg.create_task(noop())
            await task
            tg.cancel()

        assert task.done() is True
        assert task.cancelled() is False
