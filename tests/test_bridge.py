import asyncio
import threading
from collections.abc import Awaitable

import pytest

from asyncio_extensions import iscoroutinefunction
from asyncio_extensions.bridge import asyncify, markcoroutinefunction

pytestmark = pytest.mark.asyncio


async def test_asyncify_sync_returns_awaitable() -> None:
    def add(a: int, b: int) -> int:
        return a + b

    result = asyncify(add)(1, 2)

    assert isinstance(result, Awaitable)
    assert await result == add(1, 2)


async def test_asyncify_sync_runs_in_thread() -> None:
    caller_thread = threading.current_thread()
    func_thread: threading.Thread | None = None

    def capture_thread() -> None:
        nonlocal func_thread
        func_thread = threading.current_thread()

    await asyncify(capture_thread)()

    assert func_thread is not None
    assert func_thread is not caller_thread


async def test_asyncify_sync_preserves_wraps_metadata() -> None:
    def my_func() -> None:
        """My docstring."""

    wrapped = asyncify(my_func)

    assert wrapped.__name__ == "my_func"
    assert wrapped.__doc__ == "My docstring."


async def test_asyncify_async_returns_same_function() -> None:
    async def coro() -> int:
        return 42

    assert asyncify(coro) is coro


async def test_asyncify_as_decorator_on_sync() -> None:
    @asyncify
    def multiply(a: int, b: int) -> int:
        return a * b

    result = await multiply(3, 4)

    assert result == 12  # noqa: PLR2004


async def test_asyncify_as_decorator_on_async() -> None:
    @asyncify
    async def subtract(a: int, b: int) -> int:
        return a - b

    result = await subtract(10, 3)

    assert result == 7  # noqa: PLR2004


async def test_asyncify_decorator_preserves_name() -> None:
    @asyncify
    def named_func() -> None:
        """Has a name."""

    assert named_func.__name__ == "named_func"
    assert named_func.__doc__ == "Has a name."


async def test_asyncify_decorator_runs_sync_in_thread() -> None:
    caller_thread = threading.current_thread()
    seen_thread: threading.Thread | None = None

    @asyncify
    def work() -> None:
        nonlocal seen_thread
        seen_thread = threading.current_thread()

    await work()

    assert seen_thread is not None
    assert seen_thread is not caller_thread


async def test_asyncify_decorator_concurrent_calls() -> None:
    results: list[int] = []

    @asyncify
    def append(value: int) -> None:
        results.append(value)

    await asyncio.gather(append(1), append(2), append(3))

    assert sorted(results) == [1, 2, 3]


async def test_markcoroutinefunction_marks_callable() -> None:
    def sync_func() -> int:
        async def f() -> int:
            return 1

        return f()

    marked = markcoroutinefunction(sync_func)

    assert marked is sync_func
    assert iscoroutinefunction(marked) is True
    assert await marked() == 1
