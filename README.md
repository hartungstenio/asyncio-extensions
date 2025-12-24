# asyncio-extensions

[![PyPI - Version](https://img.shields.io/pypi/v/asyncio-extensions.svg)](https://pypi.org/project/asyncio-extensions)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asyncio-extensions.svg)](https://pypi.org/project/asyncio-extensions)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/hartungstenio/asyncio-extensions/main.svg)](https://results.pre-commit.ci/latest/github/hartungstenio/asyncio-extensions/main)

-----

## Installation

```console
pip install asyncio-extensions
```

## Usage

### TaskGroup
`asyncio-extensions` provide a cancellable version of AsyncIO's `TaskGroup`.

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

### checkpoint
The `checkpoint` function yields control do the event loop. It is a more elegant approach to do-nothing tasks since they give a chance for other tasks to run.

```python
from asyncio_extensions import checkpoint

class DummyChannel:
    async def send_message(self, message):
        await checkpoint()
```

### sleep_forever
The `sleep_forever` function never returns. It simply keeps yielding control do the event loop.

```python
from asyncio_extensions import sleep_forever

class DummyChannel:
    async def receive_message(self):
        await sleep_forever()
```

### noop
`noop` works just like `checkpoint`, but it is intended to be used as callback to other processes.

It accepts any number of positional and keyworks arguments, and simply yield control to the event loop once.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.


## License

`asyncio-extensions` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
