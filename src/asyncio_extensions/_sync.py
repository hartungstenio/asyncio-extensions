"""Utilities for bridging synchronous and asynchronous code."""

import asyncio
from collections.abc import AsyncIterable, Awaitable, Callable, Coroutine, Iterable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast, overload

from ._compat import TypeIs, iscoroutinefunction
from ._compat import markcoroutinefunction as _markcoroutinefunction
from ._scheduling import checkpoint

_P = ParamSpec("_P")
_R = TypeVar("_R")
_T = TypeVar("_T")


def is_awaitable(
    func: Callable[_P, _R] | Callable[_P, Awaitable[_R]],
) -> TypeIs[Callable[_P, Awaitable[_R]]]:
    """Return ``True`` if *func* is a coroutine function."""
    return iscoroutinefunction(func)


@overload
def asyncify(func: Callable[_P, Awaitable[_R]], /) -> Callable[_P, Awaitable[_R]]: ...


@overload
def asyncify(func: Callable[_P, _R], /) -> Callable[_P, Awaitable[_R]]: ...


def asyncify(func: Callable[_P, _R] | Callable[_P, Awaitable[_R]], /) -> Callable[_P, Awaitable[_R]]:
    """Ensure that a callable can be awaited.

    If *func* is already a coroutine function, return it unchanged.
    Otherwise, wrap it with :func:`asyncio.to_thread` so that calls
    run *func* in a separate thread.

    Args:
        func: A synchronous callable or coroutine function.

    Returns:
        A callable with the same signature as *func* that returns an
        :class:`~collections.abc.Awaitable`.
    """
    if is_awaitable(func):
        return func

    @wraps(func)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


def markcoroutinefunction(f: Callable[_P, _R]) -> Callable[_P, Coroutine[Any, Any, _R]]:
    """Mark *f* as a coroutine function without making it async.

    After marking, :func:`asyncio.iscoroutinefunction` returns ``True``
    for *f* even though it is a plain callable.

    Args:
        f: The callable to mark.

    Returns:
        *f* with its coroutine marker set.
    """
    return cast("Callable[_P, Coroutine[Any, Any, _R]]", _markcoroutinefunction(f))


async def identity(arg: _T) -> _T:
    """Yield to the event loop once, then return *arg* unchanged."""
    await checkpoint()
    return arg


def asyncify_iterable(itr: AsyncIterable[_T] | Iterable[_T]) -> AsyncIterable[_T]:
    """Return *itr* as an :class:`~collections.abc.AsyncIterable`.

    If *itr* is already an :class:`~collections.abc.AsyncIterable`, return it
    unchanged. Otherwise, wrap it in an async generator that yields each item
    and calls :func:`checkpoint` between items to avoid monopolising the event
    loop on large inputs.

    Args:
        itr: A synchronous or asynchronous iterable.

    Returns:
        An :class:`~collections.abc.AsyncIterable` producing the same items as *itr*.
    """
    if isinstance(itr, AsyncIterable):
        return itr

    async def gen() -> AsyncIterable[_T]:
        for it in itr:
            yield it
            await checkpoint()

    return gen()
