"""Utility functions."""

import asyncio
from collections.abc import Awaitable, Callable, Generator
from typing import Any, Never, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class _YieldToEventLoop:
    """Helper class to give control back to the event loop."""

    def __await__(self) -> Generator[None, Any, None]:
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
