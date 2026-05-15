"""Utilities for async iteration: queue generators, stream merging, and safe generator cleanup."""

import asyncio
import sys
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Callable, Iterable
from contextlib import AbstractAsyncContextManager, aclosing, asynccontextmanager
from functools import wraps
from typing import Any, ParamSpec, TypeAlias, TypeVar

from ._compat import QueueShutDown
from ._sync import asyncify_iterable
from ._task_groups import TaskGroup

T = TypeVar("T")
P = ParamSpec("P")
ManagedStream: TypeAlias = AbstractAsyncContextManager[AsyncIterator[T]]
"""An async context manager that yields an :class:`~collections.abc.AsyncIterator`.

This is the return type of :func:`safe_gen` and :func:`merge_iterables`, and the
accepted parameter type of :func:`flatten_stream`.  Use it to annotate functions
that return a context-managed async stream::

    def my_stream() -> ManagedStream[int]:
        ...
"""

if sys.version_info >= (3, 13):
    from warnings import deprecated

    @deprecated("Prefer using Queue.shutdown instead.")
    class STOP:
        """Sentinel that signals the end of an :func:`iterate_queue` stream.

        Put this class in the queue to stop iteration::

            await queue.put(STOP)

        Deprecated:
            Prefer :meth:`asyncio.Queue.shutdown` on Python 3.13+.
        """


else:

    class STOP:
        """Sentinel that signals the end of an :func:`iterate_queue` stream.

        Put this class in the queue to stop iteration::

            await queue.put(STOP)
        """


async def iterate_queue(queue: asyncio.Queue[T]) -> AsyncGenerator[T]:
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
            if it is STOP:
                queue.task_done()
                break
            yield it
        except QueueShutDown:
            break
        else:
            queue.task_done()


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
    async for it in asyncify_iterable(itr):
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
            await queue.put(STOP)  # type: ignore[arg-type]

        tg.create_task(join())

        try:
            yield iterate_queue(queue)
        finally:
            tg.cancel()


def safe_gen(fn: Callable[P, AsyncGenerator[T, Any]]) -> Callable[P, ManagedStream[T]]:
    """Wrap an async generator function so it is always closed on exit.

    Async generators must be explicitly closed when iteration is abandoned early — otherwise
    they leak resources and keep running indefinitely. This decorator converts an async
    generator function into a context manager that guarantees cleanup via ``aclosing``,
    and also suppresses ``GeneratorExit`` raised inside an exception group.

    Example::

        @safe_gen
        async def iterate_slowly(times: int) -> AsyncGenerator[int]:
            for i in range(times):
                await asyncio.sleep(10)
                yield i

        async with iterate_slowly(5) as stream:
            async for item in stream:
                print(item)

                if item == 2:
                    break  # generator is closed automatically on exit
    """

    @asynccontextmanager
    @wraps(fn)
    async def decorator(*args: P.args, **kwargs: P.kwargs) -> AsyncIterator[AsyncGenerator[T]]:
        try:
            async with aclosing(fn(*args, **kwargs)) as agen:
                yield agen
        except* GeneratorExit:
            pass

    return decorator


async def flatten_stream(ctx: ManagedStream[T]) -> AsyncIterator[T]:
    """Iterate a context-managed stream without an explicit ``async with`` block.

    Enters *ctx*, iterates the resulting async iterator, and yields each item
    directly.  This lets callers treat a :data:`ManagedStream` — the return
    type of :func:`safe_gen` and :func:`merge_iterables` — as a plain async
    iterator when context-manager syntax would be cumbersome.

    ``GeneratorExit`` raised inside an exception group is suppressed so that
    early cancellation by a :class:`~asyncio.TaskGroup` propagates cleanly.

    Args:
        ctx: An async context manager whose ``__aenter__`` returns an async
            iterator (a :data:`ManagedStream`).

    Yields:
        Items from the stream provided by *ctx*.

    Example::

        async for item in flatten_stream(merge_iterables([1, 2], [3, 4])):
            print(item)

        async with aclosing(flatten_stream(merge_iterables([1, 2], [3, 4]))) as stream:
            async for item in stream:
                print(item)
    """
    try:
        async with ctx as itr:
            async for it in itr:
                yield it
    except* GeneratorExit:
        pass
