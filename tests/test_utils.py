import asyncio

import pytest
from faker import Faker

from asyncio_extensions.utils import checkpoint, sleep_forever

from .utils import noop

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
