"""Deterministic, translation-free multilingual text preparation."""
from dataclasses import dataclass, field
import re
import unicodedata

from app.pipeline.normalization import NormalizationConfig, normalize_text

@dataclass(frozen=True)
class MultilingualText:
    original: str
    normalized: str
    language: str
    confidence: float
    hints: dict[str, str] = field(default_factory=dict)

class MultilingualProcessor:
    """Normalize text without translating it or calling a language model."""
    def __init__(self, config: NormalizationConfig | None = None,
                 language_hints: dict[str, str] | None = None):
        self.config = config or NormalizationConfig()
        self.language_hints = language_hints or {}

    @staticmethod
    def detect_language(text: str, hint: str | None = None) -> tuple[str, float]:
        if hint:
            return hint, 1.0
        if not text.strip():
            return "und", 0.0
        scripts = [(r"[\u3040-\u30ff]", "ja"), (r"[\u4e00-\u9fff]", "zh"),
                   (r"[\uac00-\ud7af]", "ko"), (r"[\u0400-\u04ff]", "ru"),
                   (r"[\u0600-\u06ff]", "ar"), (r"[\u0900-\u097f]", "hi")]
        for pattern, language in scripts:
            if re.search(pattern, text):
                return language, 0.9
        return "en", 0.5

    def process(self, text: object, *, language_hint: str | None = None,
                record_id: str | None = None) -> MultilingualText:
        original = "" if text is None else str(text)
        # NFKC handles full-width units and punctuation while retaining scripts.
        canonical = unicodedata.normalize("NFKC", original)
        normalized = normalize_text(canonical, self.config)
        hint = language_hint or (self.language_hints.get(record_id, "") if record_id else "")
        language, confidence = self.detect_language(canonical, hint)
        return MultilingualText(original, normalized, language, confidence,
                                {"language_hint": hint} if hint else {})

    def normalize(self, text: object, **kwargs) -> str:
        """Convenience API for callers that only need normalized text."""
        return self.process(text, **kwargs).normalized
