import asyncio
import sys
from collections.abc import AsyncGenerator
from itertools import count

import pytest

from asyncio_extensions import checkpoint
from asyncio_extensions.queues import STOP, fill_queue, iterate_queue, merge_iterables

pytestmark = pytest.mark.asyncio


def drain(queue: asyncio.Queue[int]) -> list[int]:
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())
    return items


# iterate_queue


async def test_iterate_queue_items_in_queue_yields_in_fifo_order() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue()
    given = [10, 20, 30]

    for value in given:
        await queue.put(value)

    results: list[int] = []
    gen = iterate_queue(queue)

    while not queue.empty():
        results.append(await anext(gen))

    assert results == given


@pytest.mark.skipif(sys.version_info < (3, 13), reason="Queue shutdown only on 3.13+")
async def test_iterate_queue_queue_shutdown_stops_iteration() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue()

    for i in range(3):
        await queue.put(i)

    queue.shutdown()

    results: list[int] = [item async for item in iterate_queue(queue)]

    assert results == [0, 1, 2]


async def test_iterate_queue_empty_queue_blocks_until_item_available() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue()
    gen = iterate_queue(queue)

    async with asyncio.TaskGroup() as tg:
        get_task = tg.create_task(anext(gen))

        await checkpoint()
        assert get_task.done() is False

        await queue.put(1)
        await checkpoint()

        assert get_task.done() is True
        assert get_task.result() == 1


async def test_iterate_queue_sentinel_in_queue_stops_iteration() -> None:
    queue: asyncio.Queue[object] = asyncio.Queue()

    await queue.put(1)
    await queue.put(2)
    await queue.put(STOP)

    results = [item async for item in iterate_queue(queue)]

    assert results == [1, 2]


# fill_queue


async def test_fill_queue_sync_iterable_fills_queue() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue()

    await fill_queue([1, 2, 3], queue)

    assert drain(queue) == [1, 2, 3]


async def test_fill_queue_async_iterable_fills_queue() -> None:
    async def source() -> AsyncGenerator[int]:
        for value in [4, 5, 6]:
            yield value

    queue: asyncio.Queue[int] = asyncio.Queue()

    await fill_queue(source(), queue)

    assert drain(queue) == [4, 5, 6]


async def test_fill_queue_empty_iterable_queue_remains_empty() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue()

    await fill_queue([], queue)

    assert queue.empty()


async def test_fill_queue_full_queue_blocks_until_space_available() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=1)
    await queue.put(0)

    async with asyncio.TaskGroup() as tg:
        fill_task = tg.create_task(fill_queue([1], queue))

        await checkpoint()
        assert fill_task.done() is False

        queue.get_nowait()
        await checkpoint()

        assert fill_task.done() is True

    assert drain(queue) == [1]


# merge_iterables


async def test_merge_iterables_sync_iterables_yields_all_items() -> None:
    async with merge_iterables([1, 2], [3, 4]) as stream:
        results = [item async for item in stream]

    assert sorted(results) == [1, 2, 3, 4]


async def test_merge_iterables_async_iterables_yields_all_items() -> None:
    async def source(values: list[int]) -> AsyncGenerator[int]:
        for v in values:
            yield v

    async with merge_iterables(source([10, 20]), source([30, 40])) as stream:
        results = [item async for item in stream]

    assert sorted(results) == [10, 20, 30, 40]


async def test_merge_iterables_single_source_yields_all_items() -> None:
    async with merge_iterables([1, 2, 3]) as stream:
        results = [item async for item in stream]

    assert results == [1, 2, 3]


async def test_merge_iterables_empty_sources_yields_nothing() -> None:
    async with merge_iterables([], []) as stream:
        results = [item async for item in stream]

    assert results == []


async def test_merge_iterables_early_exit_cancels_background_tasks() -> None:
    initial_tasks = len(asyncio.all_tasks())
    itrs = [count(), count(1)]

    async with merge_iterables(*itrs) as stream:
        assert len(asyncio.all_tasks()) > initial_tasks

        async for _ in stream:
            break

    assert len(asyncio.all_tasks()) == initial_tasks
