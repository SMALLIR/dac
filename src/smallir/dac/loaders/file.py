import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal
import tomllib
import yaml

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
                logger.debug("Found file path: %s", path)
                yield path
            elif path.is_dir():
                logger.debug(
                    "Processing directory (recursive=%s): %s",
                    self.config.recursive,
                    path,
                )
                glob_fn = path.rglob if self.config.recursive else path.glob

                # Glob specifically for each allowed extension
                for ext in self.config.allowed_extensions:
                    for file_path in glob_fn(f"*{ext}"):
                        if file_path.is_file():
                            yield file_path
            else:
                logger.error("Skipping invalid path: %s", path)

    def _filter_file_extensions(self, paths: Iterator[Path]) -> Iterator[Path]:
        """Filters paths for only supported file extensions"""
        yield from (
            path
            for path in paths
            if path.suffix.lower() in self.config.allowed_extensions
        )

    def _deduplicate_paths(self, paths: Iterator[Path]) -> Iterator[Path]:
        """Yields unique paths, using resolved paths only for duplicate tracking."""
        seen: set[Path] = set()
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path

    def _read_paths(self, paths: Iterator[Path]) -> Iterator[dict[str, Any]]:
        """Yields the filecontent and parses it using a supported parser."""
        for path in paths:
            # Get the raw content of the file
            raw_content = path.read_text(encoding="utf-8")

            # Get the right parser for this type of file
            parser = SUPPORTED_PARSERS[path.suffix.lower()]

            # Parse the raw_content
            parsed_content = parser(raw_content)

            yield parsed_content

    def load(self) -> Iterator[dict[str, Any]]:
        # Searches files that can be proccessed
        found_paths: Iterator[Path] = self._search_files()

        # Filters the paths based on the configured allowed extensions
        filtered_paths: Iterator[Path] = self._filter_file_extensions(
            paths=found_paths
        )

        # Deduplicate the paths so all files only get processed once
        deduplicated_paths: Iterator[Path] = self._deduplicate_paths(
            paths=filtered_paths
        )

        parsed_contents: Iterator[dict[str, Any]] = self._read_paths(
            paths=deduplicated_paths
        )

        yield from parsed_contents
