import asyncio
import threading
from collections.abc import Awaitable

import pytest

from asyncio_extensions import iscoroutinefunction
from asyncio_extensions._sync import asyncify, identity, is_awaitable, markcoroutinefunction

from . import noop


def test_is_awaitable_returns_true_for_coroutine_function() -> None:
    async def coro() -> None: ...

    assert is_awaitable(coro) is True


def test_is_awaitable_returns_false_for_sync_function() -> None:
    def func() -> None: ...

    assert is_awaitable(func) is False


def test_is_awaitable_returns_false_for_lambda() -> None:
    assert is_awaitable(lambda: None) is False


def test_is_awaitable_returns_true_for_markcoroutinefunction() -> None:
    def func() -> None: ...

    assert is_awaitable(markcoroutinefunction(func)) is True


@pytest.mark.asyncio
async def test_asyncify_sync_returns_awaitable() -> None:
    def add(a: int, b: int) -> int:
        return a + b

    result = asyncify(add)(1, 2)

    assert isinstance(result, Awaitable)
    assert await result == add(1, 2)


@pytest.mark.asyncio
async def test_asyncify_sync_runs_in_thread() -> None:
    caller_thread = threading.current_thread()
    func_thread: threading.Thread | None = None

    def capture_thread() -> None:
        nonlocal func_thread
        func_thread = threading.current_thread()

    await asyncify(capture_thread)()

    assert func_thread is not None
    assert func_thread is not caller_thread


@pytest.mark.asyncio
async def test_asyncify_sync_preserves_wraps_metadata() -> None:
    def my_func() -> None:
        """My docstring."""

    wrapped = asyncify(my_func)

    assert wrapped.__name__ == "my_func"
    assert wrapped.__doc__ == "My docstring."


@pytest.mark.asyncio
async def test_asyncify_async_returns_same_function() -> None:
    async def coro() -> int:
        return 42

    assert asyncify(coro) is coro


@pytest.mark.asyncio
async def test_asyncify_as_decorator_on_sync() -> None:
    @asyncify
    def multiply(a: int, b: int) -> int:
        return a * b

    result = await multiply(3, 4)

    assert result == 12  # noqa: PLR2004


@pytest.mark.asyncio
async def test_asyncify_as_decorator_on_async() -> None:
    @asyncify
    async def subtract(a: int, b: int) -> int:
        return a - b

    result = await subtract(10, 3)

    assert result == 7  # noqa: PLR2004


@pytest.mark.asyncio
async def test_asyncify_decorator_preserves_name() -> None:
    @asyncify
    def named_func() -> None:
        """Has a name."""

    assert named_func.__name__ == "named_func"
    assert named_func.__doc__ == "Has a name."


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_asyncify_decorator_concurrent_calls() -> None:
    results: list[int] = []

    @asyncify
    def append(value: int) -> None:
        results.append(value)

    await asyncio.gather(append(1), append(2), append(3))

    assert sorted(results) == [1, 2, 3]


@pytest.mark.asyncio
async def test_identity() -> None:
    async with asyncio.TaskGroup() as tg:
        task = tg.create_task(noop())

        result = await identity("x")

        assert result == "x"
        assert task.done() is True


@pytest.mark.asyncio
async def test_markcoroutinefunction_marks_callable() -> None:
    def sync_func() -> int:
        async def f() -> int:
            return 1

        return f()

    marked = markcoroutinefunction(sync_func)

    assert marked is sync_func
    assert iscoroutinefunction(marked) is True
    assert await marked() == 1
