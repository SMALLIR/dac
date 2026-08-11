from collections.abc import Iterable, Iterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Parser(Protocol):
    def parse(self, raw_content: Iterable[dict[str, Any]]) -> Iterator[Any]: ...
