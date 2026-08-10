from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

# --- Protocols (No Generics) ---


class Loader(Protocol):
    def load(self, paths: Iterable[Path]) -> Iterator[dict[str, Any]]: ...


class Parser(Protocol):
    def parse(self, raw_content: Iterable[dict[str, Any]]) -> Iterator[Any]: ...


class Transformer(Protocol):
    def transform(self, parsed_rules: Iterable[Any]) -> Iterator[dict[str, Any]]: ...


class Deployer(Protocol):
    def deploy(self, transformed_rules: Iterable[dict[str, Any]]) -> Iterator[Path]: ...


# --- Pipeline Dataclass ---


@dataclass
class Pipeline:
    loader: Loader
    parser: Parser
    transformer: Transformer
    deployer: Deployer

    def stream(self, paths: Iterable[Path]):
        raw_content = self.loader.load(paths)
        parsed_rules = self.parser.parse(raw_content)
        transformed_rules = self.transformer.transform(parsed_rules)
        self.deployer.deploy(transformed_rules)
