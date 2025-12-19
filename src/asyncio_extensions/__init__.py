import asyncio
from typing import Never

from .taskgroups import TaskGroup, TerminateTaskGroup, force_terminate_task_group
from .utils import YieldToEventLoop

__all__ = [
    "TaskGroup",
    "TerminateTaskGroup",
    "force_terminate_task_group",
    "checkpoint",
    "sleep_forever",
]


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
    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    fut = loop.create_future()

    try:
        await fut
    except:
        fut.cancel()
        raise

    msg = "should never arrive here"
    raise RuntimeError(msg)
