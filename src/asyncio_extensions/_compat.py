import sys
from collections.abc import Callable
from contextvars import Context
from typing import ParamSpec, TypedDict, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")

if sys.version_info >= (3, 12):
    from inspect import iscoroutinefunction, markcoroutinefunction
    from typing import override
else:
    from asyncio import coroutines, iscoroutinefunction

    from typing_extensions import override

    def markcoroutinefunction(f: Callable[_P, _R]) -> Callable[_P, _R]:
        f._is_coroutine = coroutines._is_coroutine  # noqa: SLF001
        return f


if sys.version_info >= (3, 13):
    from asyncio import QueueShutDown
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

    class QueueShutDown(Exception):  # noqa: N818
        pass


class _CreateTaskParams(TypedDict, total=False):
    """Parameters for creating a task in a TaskGroup."""

    name: str | None
    context: Context | None


if sys.version_info >= (3, 14):

    class CreateTaskParams(_CreateTaskParams):
        """Keyword arguments accepted by :meth:`TaskGroup.create_task`."""

        eager_start: bool | None
else:
    CreateTaskParams = _CreateTaskParams


__all__ = [
    "CreateTaskParams",
    "QueueShutDown",
    "TypeIs",
    "iscoroutinefunction",
    "markcoroutinefunction",
    "override",
]
