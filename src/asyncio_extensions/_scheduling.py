"""Utility functions."""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine, Generator
from typing import Any, Never, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

_shielded_tasks: set[asyncio.Task[Any]] = set()
"""Strong references to the shielded tasks, so they are not garbage collected while running."""


class _YieldToEventLoop:
    """Helper class to give control back to the event loop."""

    def __await__(self) -> Generator[None]:
        """Yield control to the event loop."""
        yield


async def checkpoint() -> None:
    """Yield control to the event loop.

    Equivalent to ``asyncio.sleep(0)`` but more expressive.
    """
    return await _YieldToEventLoop()


async def sleep_forever() -> Never:
    """Sleep forever, yielding to the event loop on every iteration."""
    while True:
        await _YieldToEventLoop()


async def heartbeat(
    interval: float,
    fn: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> None:
    """Call *fn* repeatedly, waiting *interval* seconds between each call.

    Args:
        interval: Number of seconds to wait between calls.
        fn: The async callable to invoke.
        *args: Positional arguments forwarded to *fn*.
        **kwargs: Keyword arguments forwarded to *fn*.
    """
    while True:
        await asyncio.sleep(interval)
        await fn(*args, **kwargs)


async def shielded(coro: Coroutine[Any, Any, T]) -> T:
    """Run *coro* in a task shielded from caller cancellation.

    If this coroutine is cancelled, the cancellation is still raised to its
    caller, but the task running *coro* continues until it completes.

    Args:
        coro: The coroutine to run.

    Returns:
        The value returned by *coro*.
    """
    task = asyncio.create_task(coro)
    _shielded_tasks.add(task)
    task.add_done_callback(_shielded_tasks.discard)
    return await asyncio.shield(task)
