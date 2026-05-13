"""Utilities for bridging synchronous and asynchronous code."""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
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

    If ``func`` is already a coroutine function, it is returned as-is.
    Otherwise, it is wrapped with :func:`asyncio.to_thread`, so that calls to
    the returned callable will run ``func`` in a separate thread and return an
    awaitable result.


    Args:
        func: A callable that is either synchronous or already a coroutine function.

    Returns:
        A callable with the same signature as ``func`` that returns an
        :class:`~collections.abc.Awaitable`.
    """
    if is_awaitable(func):
        return func

    @wraps(func)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


def markcoroutinefunction(f: Callable[_P, _R]) -> Callable[_P, Coroutine[Any, Any, _R]]:
    """Mark a callable as a coroutine function.

    Args:
        f: The callable to mark as a coroutine function.

    Returns:
        The callable marked as a coroutine function.
    """
    return cast("Callable[_P, Coroutine[Any, Any, _R]]", _markcoroutinefunction(f))


async def identity(arg: _T) -> _T:
    """Yield to the event loop once, then return *arg* unchanged."""
    await checkpoint()
    return arg
