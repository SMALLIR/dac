from collections.abc import Iterable, Iterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Transformer(Protocol):
    def transform(self, parsed_rules: Iterable[Any]) -> Iterator[dict[str, Any]]: ...
