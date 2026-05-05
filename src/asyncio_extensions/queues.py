"""Utilities for working with :mod:`asyncio` queues."""

import asyncio
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Iterable,
)
from contextlib import asynccontextmanager
from typing import TypeVar

from ._compat import QueueShutDown
from .taskgroups import TaskGroup

T = TypeVar("T")


Sentinel = object()


async def iterate_queue(queue: asyncio.Queue[T], *, sentinel: object = Sentinel) -> AsyncGenerator[T]:
    """Wrap an :class:`asyncio.Queue` as an async generator.

    Yields items from *queue* until the queue is shut down via
    :class:`asyncio.QueueShutDown` (Python 3.13+), calling
    :meth:`~asyncio.Queue.task_done` after each successful yield.

    Args:
        queue: The queue to iterate over.

    Yields:
        Items dequeued from *queue* in FIFO order.

    Example::

        async for item in iterate_queue(q):
            process(item)
    """
    while True:
        try:
            it = await queue.get()
            if it is sentinel:
                queue.task_done()
                break
            yield it
        except QueueShutDown:
            break
        else:
            queue.task_done()


def _ensure_async_iterable(itr: AsyncIterable[T] | Iterable[T]) -> AsyncIterable[T]:
    if isinstance(itr, AsyncIterable):
        return itr

    async def gen() -> AsyncIterable[T]:
        for it in itr:
            yield it

    return gen()


async def fill_queue(itr: AsyncIterable[T] | Iterable[T], queue: asyncio.Queue[T]) -> None:
    """Fill *queue* with all items from *itr*.

    Accepts both sync and async iterables and puts each item into *queue*,
    blocking if the queue is full until space becomes available.

    Args:
        itr: The source iterable (sync or async) to consume.
        queue: The queue to fill.

    Example::

        await fill_queue(range(10), q)
    """
    async for it in _ensure_async_iterable(itr):
        await queue.put(it)


@asynccontextmanager
async def merge_iterables(
    *itrs: AsyncIterable[T] | Iterable[T],
) -> AsyncIterator[AsyncGenerator[T]]:
    """Merge multiple iterables into a single async stream.

    Feeds all *itrs* into a shared queue concurrently and yields a single
    async generator that interleaves their items as they arrive. Each
    iterable is consumed in its own task, so async sources can produce
    items in parallel.

    This is an async context manager; the background producer tasks are
    cancelled and awaited on exit.

    Args:
        *itrs: Any number of sync or async iterables to merge.

    Yields:
        An async generator producing items from all *itrs* interleaved.

    Example::

        async with merge_iterables(source_a, source_b) as stream:
            async for item in stream:
                process(item)
    """
    queue = asyncio.Queue[T](len(itrs))

    async with TaskGroup() as tg:
        tasks = [tg.create_task(fill_queue(itr, queue)) for itr in itrs]

        async def join() -> None:
            await asyncio.wait(tasks)
            await queue.put(Sentinel)  # type: ignore[arg-type]

        tg.create_task(join())

        try:
            yield iterate_queue(queue)
        finally:
            tg.cancel()
