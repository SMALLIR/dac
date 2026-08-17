import re
from enum import IntEnum, StrEnum, auto
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(IntEnum):
    """Possible severities for rules."""

    INFORMATIONAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class Confidence(IntEnum):
    """Possible confidences for rules."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Priority(IntEnum):
    """Possible priorities for rules."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Status(StrEnum):
    """Possible statuses for rules."""

    EXPERIMENTAL = auto()
    TESTING = auto()
    PRODUCTION = auto()
    DEPRECATED = auto()


# Models
class Model(BaseModel):
    """The base model for all classes in this file."""

    # Configure Pydantic
    model_config = ConfigDict(
        extra="forbid",  # Instruct Pydantic to forbid extra non-defined fields when passed on instantiation.
        str_strip_whitespace=True,  # Strip leading and trailing whitespaces from string fields
        validate_default=True,  # Validate default values as well
        validate_assignment=True,  # Revalidate values when data changes after instantiation.
    )

    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump()

    def schema_to_dict(self) -> dict[str, Any]:
        """Dump the JSON Schema of the model as a dictionary."""
        return self.model_json_schema()


class Action(Model):
    """Actions that can be executed by the rule."""

    enabled: bool = Field(default=False, description="Whether the action is enabled.")
    name: str = Field(description="The name of the action.")


class Suppression(Model):
    """Suppression settings for the rule."""

    enabled: bool = Field(default=False, description="Whether the suppression is enabled.")
    time: str = Field(description="The time for the suppression.")

class Source(Model):
    """The source of the rule."""
    path: str = Field(description="The path to the rule.")

class aaaa(Model):
    ticket: str = Field(description="The ticket for the rule.")



class Search(Model):
    """Search settings for the rule."""

    platform: str = Field(description="The target platform for the search.")
    query: str = Field(description="The query for the search.")
    lookback_start: str = Field(description="The start time for the lookback period.")
    lookback_end: str | None = Field(
        default=None, description="The end time for the lookback period."
    )
    index_start: str | None = Field(
        default=None, description="The start time for the index period."
    )
    index_end: str | None = Field(
        default=None, description="The end time for the index period."
    )
    suppression: Suppression | None = Field(
        default=None, description="The suppression for the search."
    )
    actions: list[Action] = Field(
        default_factory=list, description="The list of actions for the search."
    )


class Metadata(Model):
    # REGEX patterns the validators can use
    MITRE_TECHNIQUES_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^T[1-9]\d{3}(?:\.\d{3})?$"
    )

    # Validators for the class
    @field_validator("mitre_techniques")
    @classmethod
    def validate_mitre_techniques_format(cls, mitre_techniques: list[str]) -> list[str]:
        for technique in mitre_techniques:
            if not cls.MITRE_TECHNIQUES_REGEX.match(technique):
                raise ValueError(
                    f"Mitre technique '{technique}' must follow the format: '{cls.MITRE_TECHNIQUES_REGEX.pattern}'"
                )
        return mitre_techniques

    # Fields for the class
    guid: UUID = Field(description="The unique identifier for the rule.")
    enabled: bool = Field(description="Whether the rule is enabled.")
    id: str = Field(description="The internal identifier for the rule.")
    name: str = Field(description="The name of the rule.")
    description: str = Field(description="The description of the rule.")
    severity: Severity = Field(description="The severity of the rule.")
    confidence: Confidence = Field(description="The confidence of the rule.")
    priority: Priority = Field(description="The priority of generated alerts.")
    mitre_techniques: list[str] = Field(
        min_length=1, description="The MITRE techniques for the rule."
    )
    labels: list[str] = Field(min_length=1, description="The labels for the rule.")


class Definition(Model):
    """The Definition container combining all data for a rule."""
    source: Source = Field(description="The source of the rule.")

    metadata: Metadata
    searches: list[Search] = Field(
        min_length=1, description="The searches for the rule."
    )
