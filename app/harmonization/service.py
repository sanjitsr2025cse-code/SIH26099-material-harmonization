"""Small dependency-free record orchestration for Milestone 2 smoke usage."""
from typing import Any, Iterable

from app.harmonization.embeddings import Embedder, HashingEmbedder
from app.harmonization.multilingual import MultilingualProcessor

def harmonize_record(record: dict[str, Any], processor: MultilingualProcessor | None = None,
                     embedder: Embedder | None = None) -> dict[str, Any]:
    processor = processor or MultilingualProcessor()
    embedder = embedder or HashingEmbedder()
    result = dict(record)
    text = record.get("description", record.get("original_description", ""))
    processed = processor.process(text, language_hint=record.get("language"))
    result.setdefault("original_description", processed.original)
    result["normalized_description"] = processed.normalized
    result["language"] = processed.language
    result["language_confidence"] = processed.confidence
    result["embedding"] = embedder.embed(processed.normalized)
    # Extraction is deliberately preserved rather than silently overwritten.
    result.setdefault("extracted_attributes", record.get("attributes", {}))
    return result

def harmonize_records(records: Iterable[dict[str, Any]], **kwargs) -> list[dict[str, Any]]:
    return [harmonize_record(record, **kwargs) for record in records]
