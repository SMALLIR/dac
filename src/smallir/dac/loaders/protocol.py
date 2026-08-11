from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Loader(Protocol):
    def load(self) -> Iterator[dict[str, Any]]: ...
