"""Schema and record-level validation without mutating source data."""
from collections.abc import Mapping
import pandas as pd
from app.pipeline.models import ValidationResult

def validate(frame: pd.DataFrame, required_fields: tuple[str, ...] = ("description",),
             type_rules: Mapping[str, type | str] | None = None) -> ValidationResult:
    errors, warnings = [], []
    missing = [f for f in required_fields if f not in frame.columns]
    for field in missing:
        errors.append({"code": "missing_field", "field": field, "message": f"Required field '{field}' is missing"})
    rules = type_rules or {}
    for field, expected in rules.items():
        if field not in frame:
            continue
        for index, value in frame[field].items():
            if pd.isna(value):
                continue
            ok = (isinstance(value, expected) if isinstance(expected, type)
                  else str(expected).lower() in str(frame[field].dtype).lower())
            if not ok:
                errors.append({"code": "invalid_type", "field": field, "row": index,
                               "expected": str(expected), "value": value})
    for field in required_fields:
        if field in frame:
            for index, value in frame[field].items():
                if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                    errors.append({"code": "missing_value", "field": field, "row": index,
                                   "message": "Required value is empty"})
    duplicate_count = int(frame.duplicated().sum())
    if duplicate_count:
        warnings.append({"code": "duplicate_rows", "count": duplicate_count})
    invalid_indexes = {e["row"] for e in errors if "row" in e}
    return ValidationResult(not errors, errors, warnings, len(frame), len(frame) - len(invalid_indexes))
