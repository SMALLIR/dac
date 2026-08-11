from collections.abc import Iterable, Iterator
from typing import Any

from smallir.dac.parsers.protocol import Parser


class TestParser(Parser):

    def parse(self, raw_content: Iterable[dict[str, Any]]) -> Iterator[Any]: ...
