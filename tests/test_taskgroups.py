import asyncio
import sys
from contextvars import copy_context

import pytest

from asyncio_extensions import checkpoint
from asyncio_extensions.taskgroups import (
    LimitedTaskGroup,
    TaskGroup,
    TerminateTaskGroup,
    force_terminate_task_group,
)

from . import noop

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


class TestLimitedTaskGroup:
    async def test_limits_concurrency(self) -> None:
        max_concurrent = 3
        current_concurrent = 0
        peak_concurrent = 0

        async def task() -> None:
            nonlocal current_concurrent, peak_concurrent
            current_concurrent += 1
            peak_concurrent = max(peak_concurrent, current_concurrent)
            await checkpoint()
            current_concurrent -= 1

        async with LimitedTaskGroup(max_concurrent=max_concurrent) as tg:
            for _ in range(100):
                tg.create_task(task())

        assert peak_concurrent <= max_concurrent

    async def test_create_task_params(self) -> None:
        ctx = copy_context()
        async with LimitedTaskGroup(max_concurrent=2) as tg:
            task = tg.create_task(noop(), name="test_task", context=ctx)

        assert task.get_name() == "test_task"

        if sys.version_info >= (3, 12):
            assert task.get_context() is ctx

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="Requires Python 3.14+")
    async def test_create_task_params_eager(self) -> None:
        ctx = copy_context()
        async with LimitedTaskGroup(max_concurrent=2) as tg:
            task = tg.create_task(
                noop(),
                name="test_task",
                context=ctx,
                eager_start=True,
            )
            tg.cancel()

        assert task.get_name() == "test_task"
        assert task.get_context() is ctx
        assert task.done() is True

    async def test_can_cancel(self) -> None:
        tg = LimitedTaskGroup(max_concurrent=2)
        assert hasattr(tg, "cancel")
        assert callable(tg.cancel)
