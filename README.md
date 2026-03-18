# asyncio-extensions

[![PyPI - Version](https://img.shields.io/pypi/v/asyncio-extensions.svg)](https://pypi.org/project/asyncio-extensions)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asyncio-extensions.svg)](https://pypi.org/project/asyncio-extensions)
[![codecov](https://codecov.io/github/hartungstenio/asyncio-extensions/graph/badge.svg?token=1MEZ4NBUJH)](https://codecov.io/github/hartungstenio/asyncio-extensions)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/hartungstenio/asyncio-extensions/main.svg)](https://results.pre-commit.ci/latest/github/hartungstenio/asyncio-extensions/main)

-----

## Installation

```console
pip install asyncio-extensions
```

## Usage

### TaskGroup

`asyncio-extensions` provides a cancellable version of AsyncIO's `TaskGroup`.

```python
import asyncio

from asyncio_extensions import TaskGroup

queue = asyncio.Queue()
async with TaskGroup() as tg:
    for _ in range(10):
        tg.create_task(consume_from_queue(queue))

    await add_to_queue(queue)
    await queue.join()
    tg.cancel()
```

#### LimitedTaskGroup

A version of `TaskGroup` that limits the number of concurrently running tasks.

```python
import asyncio

from asyncio_extensions import LimitedTaskGroup

queue = asyncio.Queue()
async with LimitedTaskGroup(3) as tg:
    for _ in range(50):
        tg.create_task(some_expensive_operation(queue))

    await add_to_queue(queue)
    await queue.join()
    tg.cancel()
```

### checkpoint

The `checkpoint` function yields control to the event loop. It is a more elegant approach to do-nothing tasks, giving other tasks a chance to run.

```python
from asyncio_extensions import checkpoint

class DummyChannel:
    async def send_message(self, message):
        await checkpoint()
```

### sleep_forever

The `sleep_forever` function never returns. It simply keeps yielding control to the event loop.

```python
from asyncio_extensions import sleep_forever

class DummyChannel:
    async def receive_message(self):
        await sleep_forever()
```

### heartbeat

The `heartbeat` function runs a given callable at a regular interval.

```python
from asyncio_extensions import heartbeat

async def ping():
    pass

async with TaskGroup() as tg:
    tg.create_task(heartbeat(5, ping))

    await some_long_running_process()
```

### asyncify

The `asyncify` function ensures a callable can be awaited. If the callable is already a coroutine function, it is returned as-is. Otherwise, it is wrapped so that calls run in a separate thread.

```python
from asyncio_extensions import asyncify

def blocking_read(path: str) -> str:
    with open(path) as f:
        return f.read()

async def main():
    content = await asyncify(blocking_read)("data.txt")
```

It can also be used as a decorator:

```python
from asyncio_extensions import asyncify

@asyncify
def blocking_read(path: str) -> str:
    with open(path) as f:
        return f.read()

async def main():
    content = await blocking_read("data.txt")
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

`asyncio-extensions` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
