"""Milestone 3 governed material registry and review workflow.

The product layer is intentionally in-memory and deterministic.  It builds on
``app.pipeline`` and ``app.harmonization`` without introducing a database or
an ML clustering dependency.
"""

from app.product.evaluation import EvaluationMetrics, evaluate_decisions
from app.product.models import (
    AIDecision,
    CanonicalMaterial,
    HumanDecision,
    MappingEvent,
    ReviewItem,
)
from app.product.registry import MaterialRegistry
from app.product.review import ReviewWorkflow

__all__ = [
    "AIDecision",
    "CanonicalMaterial",
    "EvaluationMetrics",
    "HumanDecision",
    "MappingEvent",
    "MaterialRegistry",
    "ReviewItem",
    "ReviewWorkflow",
    "evaluate_decisions",
]
