import logging
import yaml
import json
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# Map the file extensions to the parser methods
SUPPORTED_PARSERS = {
    ".yaml": yaml.safe_load,
    ".yml": yaml.safe_load,
    ".json": json.loads,
    ".toml": tomllib.loads,
}

# Extract the supported file extensions from the SUPPORTED_PARSERS for type annotation
SupportedFileExtensions = Literal[*SUPPORTED_PARSERS]


class FileLoaderConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DAC_LOADER_",
        frozen=True,
        extra="forbid",
    )

    paths: list[Path] = Field(description="Target files, directories, or glob patterns")

    allowed_extensions: set[SupportedFileExtensions] = Field(
        description="Allowed for this loader, supported extensions are: {SupportedFileExtensions}"
    )

    recursive: bool = Field(
        description="Whether to recursively load files from directories"
    )

    patch: bool = Field(description="Whether to patch the files")


class FileLoader(BaseModel):
    config: FileLoaderConfig = Field(default_factory=FileLoaderConfig)

    def _search_files(self) -> Iterator[Path]:
        """Yields candidate paths from direct files or targeted directory scans."""
        for path in self.config.paths:
            if path.is_file():
                logger.debug(f"Found file path: {path}")
                yield path
            elif path.is_dir():
                logger.debug(
                    f"Processing directory (recursive={self.config.recursive}): {path}"
                )
                glob_fn = path.rglob if self.config.recursive else path.glob

                # Glob specifically for each allowed extension
                for ext in self.config.allowed_extensions:
                    for item in glob_fn(f"*{ext}"):
                        if item.is_file():
                            yield item
            else:
                logger.error("Skipping invalid path: %s", path)

    def _filter_file_extensions(self, paths: Iterator[Path]) -> Iterator[Path]:
        """Filters paths for only supported file extensions"""
        yield from (
            path
            for path in paths
            if path.suffix.lower() in self.config.allowed_extensions
        )

    def _resolve_absolute_paths(self, paths: Iterator[Path]) -> Iterator[Path]:
        """Resolves the absolute path of the files"""
        yield from (path.resolve() for path in paths)

    def _deduplicate_paths(self, paths: Iterator[Path]) -> Iterator[Path]:
        """Yields unique paths, discarding any duplicate absolute paths."""
        seen: set[Path] = set()
        for path in paths:
            if path not in seen:
                seen.add(path)
                yield path

    def load(self) -> Iterator[dict[str, Any]]:
        # Searches files that can be proccessed
        resolved_paths: Iterator[Path] = self._search_files()

        # Filters the paths based on the configured allowed extensions
        filtered_paths: Iterator[Path] = self._filter_file_extensions(
            paths=resolved_paths
        )

        # Resolve the paths to absolute paths to prevent multiple references to the same paths
        resolved_paths: Iterator[Path] = self._resolve_absolute_paths(
            paths=filtered_paths
        )

        # Deduplicate the paths so all files only get processed once
        deduplicate_paths: Iterator[Path] = self._deduplicate_paths(paths=resolved_paths)

        # Itterate over the paths and load them using the correct parser
        for path in deduplicate_paths:
            print(path)
