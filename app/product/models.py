"""Small, serializable domain objects for the material registry."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIDecision:
    left_id: str
    right_id: str
    decision: str
    confidence: float
    explanation: tuple[str, ...] = ()
    semantic_score: float = 0.0
    attribute_score: float = 0.0
    terminology_score: float = 0.0


@dataclass
class CanonicalMaterial:
    cnmc_id: str
    record: dict[str, Any]
    member_ids: tuple[str, ...]
    # Registry metadata is deliberately kept alongside the canonical record so
    # callers can publish provenance without having to inspect every member.
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "ACTIVE"
    version: int = 1


@dataclass(frozen=True)
class MappingEvent:
    source_code: str
    source_system: str
    cnmc_id: str
    material_record_id: str
    event_type: str = "MAPPED"
    sequence: int = 0
    source_description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewItem:
    review_id: str
    left_id: str
    right_id: str
    ai_decision: AIDecision
    status: str = "PENDING"
    human_decision: "HumanDecision | None" = None


@dataclass(frozen=True)
class HumanDecision:
    action: str  # APPROVE, REJECT, or OVERRIDE
    reviewer: str
    explanation: str = ""
    target_cnmc_id: str | None = None
