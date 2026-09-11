"""Rule-based technical attribute extraction and validation."""
from dataclasses import dataclass, field
import re
from typing import Any

@dataclass
class ExtractionConfig:
    patterns: dict[str, str] = field(default_factory=dict)
    dictionary: dict[str, dict[str, str]] = field(default_factory=dict)
    rules: list[dict[str, Any]] = field(default_factory=list)

def extract_attributes(text: object, config: ExtractionConfig | None = None) -> dict[str, Any]:
    text = "" if text is None else str(text)
    config = config or ExtractionConfig()
    result: dict[str, Any] = {}
    for name, pattern in config.patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[name] = match.groupdict() or match.group(0)
    lower = text.lower()
    for name, terms in config.dictionary.items():
        for term, value in terms.items():
            if re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", lower):
                result[name] = value
                break
    for rule in config.rules:
        if rule.get("pattern") and re.search(rule["pattern"], text, re.IGNORECASE):
            result[rule["name"]] = rule.get("value", True)
    return result

def validate_attributes(attributes: dict[str, Any], rules: dict[str, dict[str, Any]]):
    errors = []
    for name, rule in rules.items():
        if name not in attributes:
            continue
        value = attributes[name]
        if "allowed" in rule and value not in rule["allowed"]:
            errors.append({"attribute": name, "code": "invalid_value", "value": value})
        if "unit" in rule and isinstance(value, dict) and value.get("unit") != rule["unit"]:
            errors.append({"attribute": name, "code": "invalid_unit", "value": value})
    return {"valid": not errors, "errors": errors}
