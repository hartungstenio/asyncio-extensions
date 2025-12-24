"""Utility functions."""

from collections.abc import Generator
from typing import Any, Never, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class YieldToEventLoop:
    """Helper class to give control back to the event loop."""

    def __await__(self) -> Generator[None, Any, None]:
        """Yield control to the event loop."""
        yield


async def checkpoint() -> None:
    """
    Give control back to the eventloop.

    This has the same effect of and asyncio.sleep(0), but it is more semantic
    """
    return await YieldToEventLoop()


async def sleep_forever() -> Never:
    """Sleeps forever."""
    while True:
        await YieldToEventLoop()


async def noop(*args: P.args, **kwargs: P.kwargs) -> T:
    """No-op function.

    This can be used as a callback, when nothing should be done.

    Yields control to the event loop.
    """
    return await YieldToEventLoop()
