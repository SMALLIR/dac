from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import (BaseSettings, CliPositionalArg,
                               SettingsConfigDict)


def _read_stdin() -> list[str]:
    return ["-"]


class FileLoaderConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SMALLIR_LOADER_",
        frozen=True,
        extra="forbid",
    )

    # Positional CLI arguments
    files: CliPositionalArg[list[str]] = Field(
        default_factory=_read_stdin,
        description="Target YAML files, directories, or glob patterns.",
    )


class FileLoader(BaseModel):
    config: FileLoaderConfig = Field(default_factory=FileLoaderConfig)

    def load(self) -> Iterator[dict[str, Any]]:
        print(self.config.files)
