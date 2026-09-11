"""Configurable, explainable text normalization."""
from dataclasses import dataclass, field
import re
import string

@dataclass
class NormalizationConfig:
    lowercase: bool = True
    collapse_whitespace: bool = True
    strip_punctuation: bool = False
    units: dict[str, str] = field(default_factory=dict)
    abbreviations: dict[str, str] = field(default_factory=dict)
    synonyms: dict[str, str] = field(default_factory=dict)

def normalize_text(value: object, config: NormalizationConfig | None = None) -> str:
    if value is None:
        return ""
    config = config or NormalizationConfig()
    text = str(value).strip()
    if config.lowercase:
        text = text.lower()
    replacements = {**config.units, **config.abbreviations, **config.synonyms}
    for source, target in sorted(replacements.items(), key=lambda pair: -len(pair[0])):
        text = re.sub(r"(?<!\w)" + re.escape(source) + r"(?!\w)", target, text, flags=re.IGNORECASE)
    if config.strip_punctuation:
        text = text.translate(str.maketrans("", "", string.punctuation))
    if config.collapse_whitespace:
        text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_frame(frame, description_field: str = "description",
                    config: NormalizationConfig | None = None):
    result = frame.copy()
    if "original_description" not in result.columns and description_field in result.columns:
        result["original_description"] = result[description_field]
    result["normalized_description"] = result[description_field].map(lambda x: normalize_text(x, config))
    return result
