"""The entrypoint into the DAC application."""

import logging
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, ImportString, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from smallir.dac.deployers.protocol import Deployer
from smallir.dac.loaders.protocol import Loader
from smallir.dac.parsers.protocol import Parser
from smallir.dac.pipeline import Pipeline
from smallir.dac.transformers.protocol import Transformer

# Initialize logger
logger = logging.getLogger(__name__)

# Set available log levels in a Literal
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class EnvironmentConfig(BaseSettings):
    """Configuration for loading environment variables from .env files."""

    @field_validator("env_file")
    @classmethod
    def _validate_env_files(cls, files: list[Path]) -> list[Path]:
        for path in files:
            if not path.exists():
                raise ValueError(f"Environment file does not exist: '{path}'")
            if not path.is_file():
                raise ValueError(
                    f"Environment file path is not a regular file: '{path}'"
                )
        return files

    model_config: SettingsConfigDict = SettingsConfigDict(
        title="SMALLIR-DAC",
        cli_parse_args=True,
        cli_enforce_required=True,
        extra="forbid",
        frozen=True,
    )

    env_file: list[Path] = Field(
        default_factory=list,
        validation_alias=AliasChoices("env_file", "e", "env"),
        description="List of environment files to load",
    )

    def load(self) -> None:
        """Applies all configured .env files to os.environ in order."""
        for path in self.env_file:
            load_dotenv(dotenv_path=path, override=True)


class PipelineConfig(BaseSettings):
    """Configuration for the pipeline components."""

    @field_validator("loader")
    @classmethod
    def _validate_loader(cls, loader: type[Loader]) -> type[Loader]:
        if not issubclass(loader, Loader):
            raise TypeError(
                f"Class '{loader.__qualname__}' does not implement the '{Loader.__name__}' protocol"
            )
        return loader

    @field_validator("parser")
    @classmethod
    def _validate_parser(cls, parser: type[Parser]) -> type[Parser]:
        if not issubclass(parser, Parser):
            raise TypeError(
                f"Class '{parser.__qualname__}' does not implement the '{Parser.__name__}' protocol"
            )
        return parser

    @field_validator("transformer")
    @classmethod
    def _validate_transformer(cls, transformer: type[Transformer]) -> type[Transformer]:
        if not issubclass(transformer, Transformer):
            raise TypeError(
                f"Class '{transformer.__qualname__}' does not implement the '{Transformer.__name__}' protocol"
            )
        return transformer

    @field_validator("deployer")
    @classmethod
    def _validate_deployer(cls, deployer: type[Deployer]) -> type[Deployer]:
        if not issubclass(deployer, Deployer):
            raise TypeError(
                f"Class '{deployer.__qualname__}' does not implement the '{Deployer.__name__}' protocol"
            )
        return deployer

    model_config = SettingsConfigDict(
        env_prefix="DAC_PIPELINE_",
        extra="forbid",
        frozen=True,
    )

    log_level: LogLevel = Field(
        default="INFO",
        description="The logging level",
    )

    loader: ImportString = Field(
        description="The loader to load the detection rules",
    )

    parser: ImportString = Field(
        description="The parser to parse the detection rules",
    )

    transformer: ImportString = Field(
        description="The transformer to transform the detection rules",
    )

    deployer: ImportString = Field(
        description="The deployer to deploy the detection rules",
    )


def entrypoint() -> None:
    """The entrypoint of the smallir-dac CLI."""
    # Parse dotenv paths via CLI arguments.
    # After dotenv path validation load the files.
    environment_config: EnvironmentConfig = EnvironmentConfig()
    environment_config.load()

    # Parse pipeline components and log level via DAC_PIPELINE_* env variables.
    pipeline_config: PipelineConfig = PipelineConfig()

    # Configure root logging with the level specified in DAC_PIPELINE_LOG_LEVEL
    logging.basicConfig(
        level=pipeline_config.log_level,
        format='timestamp="%(asctime)s" level="%(levelname)s" logger="%(name)s" msg="%(message)s"',
        datefmt="%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 timestamp with timezone offset
        force=True,  # Overrides any early-initialized default handlers
    )
    logger.debug("Logger initialized with level: %s", pipeline_config.log_level)

    # Initialize pipeline components to prepare them for dependency injection.
    loader: Loader = pipeline_config.loader()
    parser: Parser = pipeline_config.parser()
    transformer: Transformer = pipeline_config.transformer()
    deployer: Deployer = pipeline_config.deployer()

    # Inject the pipeline components into the pipeline and initialize it.
    pipeline: Pipeline = Pipeline(
        loader=loader, parser=parser, transformer=transformer, deployer=deployer
    )
    pipeline.run()


if __name__ == "__main__":
    # If smallir-dac is run as a script, call the entrypoint function.
    entrypoint()
