import asyncio
from collections.abc import Generator
from typing import Any, Never


class YieldToEventLoop:
    """Helper class to give control back to the event loop."""

    def __await__(self) -> Generator[None, Any, None]:
        yield


async def checkpoint() -> None:
    """
    Give control back to the eventloop.

    This has the same effect of and asyncio.sleep(0), but it is more semantic
    """
    return await YieldToEventLoop()


async def sleep_forever() -> Never:
    """
    Sleeps forever.
    """
    while True:
        await YieldToEventLoop()
