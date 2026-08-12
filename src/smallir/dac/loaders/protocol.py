from collections.abc import Iterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Loader(Protocol):
    def load(self) -> Iterator[dict[str, Any]]: ...
