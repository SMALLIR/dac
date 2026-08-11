from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Deployer(Protocol):
    def deploy(self, transformed_rules: Iterable[dict[str, Any]]) -> Iterator[Path]: ...
