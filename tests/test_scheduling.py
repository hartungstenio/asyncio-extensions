import asyncio
import threading
from contextlib import suppress
from unittest import mock

import pytest
from faker import Faker

from asyncio_extensions import TaskGroup
from asyncio_extensions._scheduling import checkpoint, heartbeat, shielded, sleep_forever

from . import noop

pytestmark = pytest.mark.asyncio


async def test_checkpoint() -> None:
    async with asyncio.TaskGroup() as tg:
        task = tg.create_task(noop())

        await checkpoint()

        assert task.done() is True


async def test_sleep_forever(faker: Faker) -> None:
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(faker.random_int(1, 10)):
            await sleep_forever()


async def test_sleep_forever_cycles_event_loop(faker: Faker) -> None:
    with pytest.raises(TimeoutError):  # noqa: PT012
        async with (
            asyncio.timeout(faker.random_int(1, 10)),
            asyncio.TaskGroup() as tg,
        ):
            tasks = [tg.create_task(asyncio.sleep(i)) for i in range(7)]
            await sleep_forever()

    assert all(t.done() for t in tasks)
    assert not any(t.cancelled() for t in tasks)


async def test_heartbeat() -> None:
    mock_fn = mock.AsyncMock()
    with suppress(TimeoutError):
        async with asyncio.timeout(5):
            await heartbeat(1, mock_fn, 1, 2, name="a")

    assert mock_fn.await_args_list == [mock.call(1, 2, name="a")] * 4


async def test_heartbeat_sync_function_runs_in_thread() -> None:
    event_loop_thread = threading.get_ident()
    started = threading.Event()
    calls: list[tuple[int, int, int, str]] = []

    def mock_fn(first: int, second: int, *, name: str) -> None:
        calls.append((threading.get_ident(), first, second, name))
        started.set()

    task = asyncio.create_task(heartbeat(0, mock_fn, 1, 2, name="a"))
    try:
        assert await asyncio.to_thread(started.wait, 1)
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    assert calls
    assert all(call[1:] == (1, 2, "a") for call in calls)
    assert all(call[0] != event_loop_thread for call in calls)


async def test_shielded_returns_coroutine_result() -> None:
    assert await shielded(asyncio.sleep(0, result="result")) == "result"


async def test_shielded_task_continues_after_caller_cancellation() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    completed = asyncio.Event()

    async def work() -> None:
        started.set()
        await release.wait()
        completed.set()

    async with TaskGroup() as tg:
        tg.create_task(shielded(work()))
        await started.wait()
        tg.cancel()

    assert not completed.is_set()
    release.set()
    await completed.wait()
