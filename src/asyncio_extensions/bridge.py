"""Utilities for bridging synchronous and asynchronous code."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar, overload

from ._compat import is_awaitable

_P = ParamSpec("_P")
_R = TypeVar("_R")


@overload
def asyncify(func: Callable[_P, Awaitable[_R]], /) -> Callable[_P, Awaitable[_R]]: ...


@overload
def asyncify(func: Callable[_P, _R], /) -> Callable[_P, Awaitable[_R]]: ...


def asyncify(
    func: Callable[_P, _R] | Callable[_P, Awaitable[_R]], /
) -> Callable[_P, Awaitable[_R]]:
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
