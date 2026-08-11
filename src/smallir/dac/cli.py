from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, ImportString, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from smallir.dac.deployers.protocol import Deployer
from smallir.dac.loaders.protocol import Loader
from smallir.dac.parsers.protocol import Parser
from smallir.dac.pipeline import Pipeline
from smallir.dac.transformers.protocol import Transformer


class EnvironmentConfig(BaseSettings):
    """Configuration for loading environment variables from .env files.

    Args:
        env_file: List of environment files to load.
    """

    @field_validator("env_file")
    @classmethod
    def _validate_env_files(cls, files: list[Path]) -> list[Path]:
        for path in files:
            if not path.exists():
                raise ValueError(f"Environment dotenv cannot be found: '{path}'")
            if not path.is_file():
                raise ValueError(f"Environment dotenv is not a file: '{path}'")
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


def _validate_protocol(cls_obj: type | None, protocol: type, name: str) -> type:
    if cls_obj is None:
        raise ValueError(f"{name.capitalize()} is required")
    if not issubclass(cls_obj, protocol):
        raise ValueError(
            f"Class '{cls_obj.__qualname__}' does not implement the '{protocol.__name__}' protocol."
        )
    return cls_obj


class PipelineConfig(BaseSettings):
    """Configuration for the pipeline components.

    Args:
        loader: Loader class to load raw content.
        parser: Parser class to parse raw content.
        transformer: Transformer class to transform parsed rules.
        deployer: Deployer class to deploy transformed rules.
    """

    @field_validator("loader")
    @classmethod
    def _validate_loader(cls, v: type | None) -> type:
        return _validate_protocol(v, Loader, "loader")

    @field_validator("parser")
    @classmethod
    def _validate_parser(cls, v: type | None) -> type:
        return _validate_protocol(v, Parser, "parser")

    @field_validator("transformer")
    @classmethod
    def _validate_transformer(cls, v: type | None) -> type:
        return _validate_protocol(v, Transformer, "transformer")

    @field_validator("deployer")
    @classmethod
    def _validate_deployer(cls, v: type | None) -> type:
        return _validate_protocol(v, Deployer, "deployer")

    model_config = SettingsConfigDict(
        env_prefix="SMALLIR_PIPELINE_",
        extra="forbid",
        frozen=True,
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

    # Parse pipeline components via dotenv variables.
    pipeline_config: PipelineConfig = PipelineConfig()

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
