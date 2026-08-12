from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FileLoaderConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DAC_LOADER_",
        frozen=True,
        extra="forbid",
    )

    paths: list[Path] = Field(
        description="Target files, directories, or glob patterns"
    )

    recursive: bool = Field(
        description="Whether to recursively load files from directories"
    )

    patch: bool = Field(
        description="Whether to patch the files"
    )


class FileLoader(BaseModel):
    config: FileLoaderConfig = Field(default_factory=FileLoaderConfig)

    def load(self) -> Iterator[dict[str, Any]]:
        print(self.config.paths)
