"""Additive Milestone 2 material harmonization components."""

from app.harmonization.config import HarmonizationSettings
from app.harmonization.embeddings import (
    EmbeddingRecord,
    HashingEmbedder,
    SentenceTransformerEmbedder,
)
from app.harmonization.matching import MatchDecision, MaterialMatcher
from app.harmonization.multilingual import MultilingualProcessor
from app.harmonization.persistence import MaterialRepository, schema_sql
from app.harmonization.retrieval import InMemoryCosineIndex
from app.harmonization.service import harmonize_record, harmonize_records

__all__ = [
    "EmbeddingRecord",
    "HarmonizationSettings",
    "HashingEmbedder",
    "SentenceTransformerEmbedder",
    "MatchDecision",
    "MaterialMatcher",
    "MultilingualProcessor",
    "MaterialRepository",
    "schema_sql",
    "InMemoryCosineIndex",
    "harmonize_record",
    "harmonize_records",
]
