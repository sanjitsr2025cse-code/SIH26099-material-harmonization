"""Shared normalization for material attribute payloads."""
from __future__ import annotations

import ast
import json
import math
from typing import Any


def parse_attributes(value: Any) -> dict[str, Any]:
    """Normalize JSON, Python-literal, and mapping values to dictionaries."""
    if isinstance(value, dict):
        return value
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return {}
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return {}
    return parsed if isinstance(parsed, dict) else {}


def prepare_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize uploaded records while preserving all other values."""
    prepared = []
    for record in records:
        value = dict(record)
        if "attributes" in value:
            value["attributes"] = parse_attributes(value["attributes"])
        prepared.append(value)
    return prepared


def ingest_records(registry: Any, records: list[dict[str, Any]]) -> Any:
    """Normalize records and ingest them into the supplied registry."""
    registry.ingest(prepare_records(records))
    return registry
