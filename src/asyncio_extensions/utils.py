from collections.abc import Generator
from typing import Any


class YieldToEventLoop:
    """Helper class to give control back to the event loop."""

    def __await__(self) -> Generator[None, Any, None]:
        yield
