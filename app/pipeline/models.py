"""Typed results used by the pre-ML material pipeline."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ValidationResult:
    valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    valid_row_count: int = 0

@dataclass
class ProfileResult:
    row_count: int
    column_count: int
    columns: dict[str, dict[str, Any]]
    duplicate_rows: int
    missing_values: dict[str, int]

@dataclass
class PipelineResult:
    records: list[dict[str, Any]]
    validation: ValidationResult
    profile: ProfileResult
    dataframe: Any = None
