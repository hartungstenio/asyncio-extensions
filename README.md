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

### identity

The `identity` function yields control back to the event loop once, and then returns the value that was passed in. It is useful when you already have a cached result and want to create a task that behaves like any other asynchronous operation.

```python
from asyncio_extensions import TaskGroup, identity

async def get_product(product_id: int):
    cached_product = await product_cache.get(product_id)

    async with TaskGroup() as tg:
        if cached_product is not None:
            task = tg.create_task(identity(cached_product))
        else:
            task = tg.create_task(fetch_product_from_api(product_id))

        tg.create_task(update_search_metrics(product_id))

    product = task.result()
    return product
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

### iterate_queue

The `iterate_queue` async generator wraps an `asyncio.Queue` so it can be consumed with a plain `async for` loop. It calls `task_done()` automatically after each item and stops when the queue is shut down (Python 3.13+) or when a sentinel value is dequeued.

```python
import asyncio

from asyncio_extensions import iterate_queue

async def process_items(queue: asyncio.Queue[str]) -> None:
    async for item in iterate_queue(queue):
        print(item)
```

To signal the end of the stream, call `queue.shutdown()` from the producer (Python 3.13+):

```python
async def producer(queue: asyncio.Queue[str]) -> None:
    for item in ["a", "b", "c"]:
        await queue.put(item)
    queue.shutdown()
```

On older Python versions, put the `STOP` sentinel in the queue when done:

```python
from asyncio_extensions import iterate_queue, STOP

async def producer(queue: asyncio.Queue[object]) -> None:
    for item in ["a", "b", "c"]:
        await queue.put(item)
    await queue.put(STOP)

async def consumer(queue: asyncio.Queue[object]) -> None:
    async for item in iterate_queue(queue):
        print(item)
```

> **Note:** `STOP` is deprecated on Python 3.13+. Prefer `queue.shutdown()` instead.

### fill_queue

The `fill_queue` coroutine fills an `asyncio.Queue` from any sync or async iterable. It accepts both `Iterable` and `AsyncIterable` sources and blocks if the queue is full until space becomes available.

```python
import asyncio

from asyncio_extensions import fill_queue

async def main() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue()
    await fill_queue(range(10), queue)
```

It also works with async iterables:

```python
async def source():
    for item in fetch_from_api():
        yield item

await fill_queue(source(), queue)
```

### merge_iterables

The `merge_iterables` async context manager merges multiple sync or async iterables into a single interleaved stream, feeding all sources into a shared queue concurrently.

```python
import asyncio

from asyncio_extensions import merge_iterables

async def main() -> None:
    async with merge_iterables([1, 2, 3], [4, 5, 6]) as stream:
        async for item in stream:
            print(item)
```

It also accepts async iterables, which can produce items in parallel:

```python
async def fetch_page(page: int):
    ...  # yields items from a remote page

async with merge_iterables(fetch_page(1), fetch_page(2)) as stream:
    async for item in stream:
        process(item)
```

### iscoroutinefunction and markcoroutinefunction

The `iscoroutinefunction` helper checks whether a callable is already a coroutine function. It is re-exported from `inspect` on newer Python versions and from `asyncio` on older versions, depending on the runtime.

The `markcoroutinefunction` helper marks a normal sync callable as a coroutine function. On Python 3.12+ this is `inspect.markcoroutinefunction`, but with the return type annotated so the function can be treated as a coroutine function in type-checked code.

```python
from asyncio_extensions import iscoroutinefunction, markcoroutinefunction

async def main():
    def sync_task() -> int:
        return 42

    assert iscoroutinefunction(sync_task) is False

    marked = markcoroutinefunction(sync_task)
    assert iscoroutinefunction(marked) is True
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

`asyncio-extensions` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
