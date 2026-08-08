from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, CliPositionalArg

def _read_stdin() -> list[str]:
    ....


class StartupConfig(BaseSettings):
    """Application CLI and environment settings built entirely on Pydantic."""

    model_config = SettingsConfigDict(
        title="SMALLIR-DAC",
        cli_parse_args=True,
        env_prefix="SMALLIR_",
        cli_show_env_vars=True,
        cli_implicit_flags=True,
        cli_enforce_required=True,
    )

    # Positional CLI arguments (e.g. smallir-dac test.py rules/)
    files: CliPositionalArg[list[str]] = Field(
        default_factory=_read_stdin,
        description="Target YAML files, directories, or glob patterns.",
    )

    # Output directory flag: supports -o, --output-dir, or --output
    output_dir: Optional[Path] = Field(
        default=None,
        validation_alias=AliasChoices("o", "output_dir", "output"),
        description="Target output directory for generated rules.",
    )

    # Explicit dry run flag: supports -d or --dry-run
    dry_run: bool = Field(
        default=False,
        validation_alias=AliasChoices("d", "dry_run"),
        description="Validate and transform without writing files to disk.",
    )

    @property
    def is_dry_run(self) -> bool:
        """Dry-run is active if explicitly requested OR if no output directory was supplied."""
        return self.dry_run or self.output_dir is None


def entrypoint():
    config = StartupConfig()

    print(f"[*] Input files/targets: {config.files}")
    if config.is_dry_run:
        print("[*] Mode: DRY-RUN (no files will be written)")
    else:
        print(f"[*] Mode: DEPLOY -> Target directory: {config.output_dir}")

    return config


if __name__ == "__main__":
    entrypoint()