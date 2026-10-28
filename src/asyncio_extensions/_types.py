from collections.abc import AsyncIterable, AsyncIterator, Iterable
from contextlib import AbstractAsyncContextManager
from typing import TypeAlias, TypeVar

T = TypeVar("T")

ManagedStream: TypeAlias = AbstractAsyncContextManager[AsyncIterator[T]]
"""An async context manager that yields an :class:`~collections.abc.AsyncIterator`.

This is the return type of :func:`safe_gen` and :func:`merge_iterables`, and the
accepted parameter type of :func:`flatten_stream`.  Use it to annotate functions
that return a context-managed async stream::

    def my_stream() -> ManagedStream[int]:
        ...
"""

AnyIterable: TypeAlias = AsyncIterable[T] | Iterable[T]
"""An asynchronous or synchronous iterable of *T*."""
