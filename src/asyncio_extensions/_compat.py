import inspect
import sys
from collections.abc import Awaitable, Callable
from contextvars import Context
from typing import ParamSpec, TypedDict, TypeVar

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs


class _CreateTaskParams(TypedDict, total=False):
    """Parameters for creating a task in a TaskGroup."""

    name: str | None
    context: Context | None


if sys.version_info >= (3, 14):

    class CreateTaskParams(_CreateTaskParams):
        """Parameters for creating a task in a TaskGroup."""

        eager_start: bool | None
else:
    CreateTaskParams = _CreateTaskParams


_P = ParamSpec("_P")
_R = TypeVar("_R")


def is_awaitable(
    func: Callable[_P, _R] | Callable[_P, Awaitable[_R]],
) -> TypeIs[Callable[_P, Awaitable[_R]]]:
    return inspect.iscoroutinefunction(func)


__all__ = [
    "CreateTaskParams",
    "TypeIs",
    "is_awaitable",
    "override",
]
