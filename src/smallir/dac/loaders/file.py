import json
import logging
import tomllib
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Supported file extensions for type annotation
SupportedFileExtensions = Literal[".yaml", ".yml", ".json", ".toml"]

# Map the file extensions to the parser methods
SUPPORTED_PARSERS: dict[str, Callable[[str], Any]] = {
    ".yaml": yaml.safe_load,
    ".yml": yaml.safe_load,
    ".json": json.loads,
    ".toml": tomllib.loads,
}


class FileLoaderConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DAC_LOADER_",
        frozen=True,
        extra="forbid",
    )

    paths: list[Path] = Field(description="Target files, directories, or glob patterns")

    allowed_extensions: set[SupportedFileExtensions] = Field(
        description="Allowed for this loader, supported extensions are: .yaml, .yml, .json, .toml"
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
            try:
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
                        try:
                            for file_path in glob_fn(f"*{ext}"):
                                try:
                                    if file_path.is_file():
                                        yield file_path
                                except (PermissionError, OSError) as error:
                                    logger.error(
                                        "OS error inspecting file '%s': %s",
                                        file_path,
                                        error,
                                    )
                                except Exception as error:
                                    logger.error(
                                        "Unhandled error inspecting file '%s': %s",
                                        file_path,
                                        error,
                                    )
                        except (PermissionError, OSError) as error:
                            logger.error(
                                "Failed scanning directory '%s' for '%s': %s",
                                path,
                                ext,
                                error,
                            )
                        except Exception as error:
                            logger.error(
                                "Unhandled error scanning directory '%s': %s",
                                path,
                                error,
                            )
                else:
                    logger.error("Skipping invalid path: %s", path)

            except (PermissionError, OSError) as error:
                logger.error("Failed accessing path '%s': %s", path, error)
            except Exception as error:
                logger.error(
                    "Unhandled error while inspecting path '%s': %s", path, error
                )

    def _filter_file_extensions(self, paths: Iterable[Path]) -> Iterator[Path]:
        """Filters paths for only supported file extensions"""
        for path in paths:
            try:
                if path.suffix.lower() in self.config.allowed_extensions:
                    yield path
            except Exception as error:
                logger.error(
                    "Unhandled error filtering extension for path '%s': %s", path, error
                )

    def _deduplicate_paths(self, paths: Iterable[Path]) -> Iterator[Path]:
        """Yields unique paths, using resolved paths only for duplicate tracking."""
        seen: set[Path] = set()
        for path in paths:
            try:
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path
            except (RuntimeError, PermissionError, OSError) as error:
                logger.error(
                    "Failed resolving path '%s' for deduplication: %s", path, error
                )
            except Exception as error:
                logger.error("Unhandled error resolving path '%s': %s", path, error)

    def _read_data(self, paths: Iterable[Path]) -> Iterator[dict[str, Any]]:
        """Yields the filecontent and parses it using a supported parser."""
        for path in paths:
            ext = path.suffix.lower()
            parser = SUPPORTED_PARSERS.get(ext)

            if not parser:
                logger.error(
                    "No supported parser found for extension '%s' on file '%s'",
                    ext,
                    path,
                )
                continue

            # Read raw content from disk
            try:
                raw_content = path.read_text(encoding="utf-8")
            except (
                FileNotFoundError,
                PermissionError,
                UnicodeDecodeError,
                OSError,
            ) as error:
                logger.error("Failed reading file '%s': %s", path, error)
                continue
            except Exception as error:
                logger.error("Unhandled error reading file '%s': %s", path, error)
                continue

            # Parse the raw content
            try:
                parsed_content = parser(raw_content)
            except (
                yaml.YAMLError,
                json.JSONDecodeError,
                tomllib.TOMLDecodeError,
            ) as error:
                logger.error("Syntax error parsing %s file '%s': %s", ext, path, error)
                continue
            except Exception as error:
                logger.error("Unhandled error parsing file '%s': %s", path, error)
                continue

            # Guard dictionary contract
            if isinstance(parsed_content, dict):
                yield parsed_content
            else:
                logger.error(
                    "Skipping '%s': expected dict, got %s",
                    path,
                    type(parsed_content).__name__,
                )

    def _select_data(
        self, data: Iterable[dict[str, Any]], dot_path: Optional[str]
    ) -> Iterator[dict[str, Any]]:
        """Yields part of a dictionary based on the dot path into the dictionary structure"""
        # This method is always called by the pipeline and because of that we can skip it if we dont need to select a subpath
        if not dot_path:
            yield from data
            return # Stop the execution of the method

        for item in data:
            ...            
        



def _unpack_data(self, data: Iterable[Any]) -> Iterator[dict[str, Any]]:
    """Yields dictionaries individually, unpacking nested lists if encountered."""
    for item in data:
        if isinstance(item, list):
            for entry in item:
                if isinstance(entry, dict):
                    yield entry
                else:
                    logger.error(
                        "Skipping invalid item in list: expected dict, got %s",
                        type(entry).__name__,
                    )
        elif isinstance(item, dict):
            yield item
        else:
            logger.error(
                "Skipping invalid payload: expected dict or list, got %s",
                type(item).__name__,
            )

    def load(self) -> Iterator[dict[str, Any]]:
        # Searches files that can be processed
        found_paths: Iterator[Path] = self._search_files()

        # Filters the paths based on the configured allowed extensions
        filtered_paths: Iterator[Path] = self._filter_file_extensions(paths=found_paths)

        # Deduplicate the paths so all files only get processed once
        deduplicated_paths: Iterator[Path] = self._deduplicate_paths(
            paths=filtered_paths
        )

        parsed_contents: Iterator[dict[str, Any]] = self._read_data(
            paths=deduplicated_paths
        )

        selected_data: Iterator[dict[str, Any]] = self._select_data(
            data=parsed_contents
        )

        yield from parsed_contents
