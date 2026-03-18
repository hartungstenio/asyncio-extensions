import inspect
import sys
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

_P = ParamSpec("_P")
_R = TypeVar("_R")


def is_awaitable(
    func: Callable[_P, _R] | Callable[_P, Awaitable[_R]],
) -> TypeIs[Callable[_P, Awaitable[_R]]]:
    return inspect.iscoroutinefunction(func)


__all__ = [
    "TypeIs",
    "is_awaitable",
    "override",
]
