"""Explainable hybrid matching with explicit hard constraints."""
from dataclasses import dataclass, field
from typing import Any

from app.harmonization.retrieval import cosine_similarity
from app.harmonization.config import HarmonizationSettings

@dataclass
class MatchDecision:
    decision: str
    confidence: float
    semantic_score: float
    attribute_score: float
    terminology_score: float
    reasons: list[str] = field(default_factory=list)

@dataclass
class MatchConfig:
    equivalent_threshold: float = 0.82
    review_threshold: float = 0.58
    semantic_weight: float = 0.55
    attribute_weight: float = 0.30
    terminology_weight: float = 0.15
    hard_attributes: tuple[str, ...] = ("grade", "size", "standard", "pressure", "voltage")
    terminology: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "MatchConfig":
        settings = HarmonizationSettings.from_env()
        return cls(
            equivalent_threshold=settings.equivalent_threshold,
            review_threshold=settings.review_threshold,
        )

class MaterialMatcher:
    def __init__(self, config: MatchConfig | None = None):
        self.config = config or MatchConfig.from_env()

    def compare(self, left: dict[str, Any], right: dict[str, Any]) -> MatchDecision:
        reasons: list[str] = []
        attrs_l = (left.get("extracted_attributes") or left.get("extracted_attrs")
                   or left.get("technical_attributes") or left.get("attributes", {}))
        attrs_r = (right.get("extracted_attributes") or right.get("extracted_attrs")
                   or right.get("technical_attributes") or right.get("attributes", {}))
        conflicts = [name for name in self.config.hard_attributes
                     if name in attrs_l and name in attrs_r and str(attrs_l[name]).casefold() != str(attrs_r[name]).casefold()]
        if conflicts:
            return MatchDecision("DIFFERENT", 0.0, self._semantic(left, right), 0.0, 0.0,
                                 [f"hard constraint conflict: {name}" for name in conflicts])
        comparable = [name for name in self.config.hard_attributes if name in attrs_l and name in attrs_r]
        attribute_score = sum(str(attrs_l[n]).casefold() == str(attrs_r[n]).casefold() for n in comparable) / len(comparable) if comparable else 0.5
        for name in comparable:
            reasons.append(f"{name} matches")
        text_l = str(left.get("normalized_description", left.get("description", ""))).casefold()
        text_r = str(right.get("normalized_description", right.get("description", ""))).casefold()
        terms_l, terms_r = set(text_l.split()), set(text_r.split())
        terminology_score = len(terms_l & terms_r) / len(terms_l | terms_r) if terms_l | terms_r else 0.0
        semantic = self._semantic(left, right)
        confidence = (semantic * self.config.semantic_weight + attribute_score * self.config.attribute_weight
                      + terminology_score * self.config.terminology_weight)
        decision = "EQUIVALENT" if confidence >= self.config.equivalent_threshold else "REVIEW" if confidence >= self.config.review_threshold else "DIFFERENT"
        reasons.append(f"hybrid confidence {confidence:.3f}")
        return MatchDecision(decision, confidence, semantic, attribute_score, terminology_score, reasons)

    def match(self, left: dict[str, Any], right: dict[str, Any]) -> MatchDecision:
        return self.compare(left, right)

    compare_records = compare

    @staticmethod
    def _semantic(left, right) -> float:
        if left.get("embedding") and right.get("embedding"):
            return max(0.0, cosine_similarity(left["embedding"], right["embedding"]))
        return 1.0 if str(left.get("normalized_description", "")).casefold() == str(right.get("normalized_description", "")).casefold() else 0.0
