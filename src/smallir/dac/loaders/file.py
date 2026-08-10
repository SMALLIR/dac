class FileLoader:

    # Positional CLI arguments (e.g. smallir-dac test.py rules/)
    files: CliPositionalArg[list[str]] = Field(
        default_factory=_read_stdin,
        description="Target YAML files, directories, or glob patterns.",
    )

    # Output directory flag: supports -o or --output
    output: Optional[Path] = Field(
        default=None,
        validation_alias=AliasChoices("o", "output"),
        description="Target output directory for generated rules.",
    )

    def load(file: str): 
        ...
