from collections.abc import Iterable, Iterator
from typing import Any

from smallir.dac.transformers.protocol import Transformer


class TestTransformer(Transformer):
    def transform(self, parsed_rules: Iterable[Any]) -> Iterator[dict[str, Any]]: ...
