from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class StartupConfig(BaseSettings):
    model_config = SettingsConfigDict(title="SMALLIR-DAC", cli_parse_args=True, env_prefix="SMALLIR")

    sources: list[str] = Field(description="A list of ..")


    target: Optional[str] = Field(description="The output directory for the target files. Dry run if not set!")


def entrypoint():
    startup_config = StartupConfig()

    