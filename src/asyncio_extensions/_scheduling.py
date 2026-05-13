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
    """
    Give control back to the eventloop.

    This has the same effect of and asyncio.sleep(0), but it is more semantic
    """
    return await _YieldToEventLoop()


async def sleep_forever() -> Never:
    """Sleeps forever."""
    while True:
        await _YieldToEventLoop()


async def heartbeat(
    interval: float,
    fn: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> None:
    """Run :arg:`fn` with the given args at regular interval."""
    while True:
        await asyncio.sleep(interval)
        await fn(*args, **kwargs)
