"""Presentation adapters for the material harmonization registry."""
from __future__ import annotations

import io
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.benchmark.dataset import generate_dataset
from app.benchmark.runner import run_benchmark
from app.product.dashboard import parse_attributes
from app.product.registry import MaterialRegistry

router = APIRouter(prefix="/api/materials", tags=["materials"])
registry = MaterialRegistry()


class ReviewDecision(BaseModel):
    action: str = Field(pattern="^(APPROVE|REJECT|OVERRIDE)$")
    reviewer: str = Field(min_length=1)
    explanation: str = ""
    target_cnmc_id: str | None = None


def _record(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        data = {key: _record(getattr(value, key)) for key in value.__dataclass_fields__}
        return data
    if isinstance(value, dict):
        return {str(key): _record(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_record(item) for item in value]
    return value


def _decision_counts() -> dict[str, int]:
    counts = {"EQUIVALENT": 0, "REVIEW": 0, "DIFFERENT": 0}
    for decision in registry.decisions:
        counts[decision.decision] = counts.get(decision.decision, 0) + 1
    return counts


def _validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    missing = sum(not str(item.get("description", "")).strip() for item in records)
    fingerprints = [str(sorted(item.items())) for item in records]
    duplicates = len(fingerprints) - len(set(fingerprints))
    return {"rows": len(records), "columns": list(records[0]) if records else [], "missing_descriptions": missing, "duplicate_rows": duplicates, "valid": bool(records) and missing == 0}


@router.get("/overview")
def overview() -> dict[str, Any]:
    return {"statistics": registry.statistics(), "decision_counts": _decision_counts(), "health": "operational"}


@router.post("/upload")
async def upload_materials(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or "upload.csv"
    payload = await file.read()
    try:
        import pandas as pd
        frame = pd.read_csv(io.BytesIO(payload)) if filename.lower().endswith(".csv") else pd.read_excel(io.BytesIO(payload))
        records = [{key: (parse_attributes(value) if key == "attributes" else value) for key, value in row.items()} for row in frame.to_dict("records")]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to read {filename}: {exc}") from exc
    validation = _validation(records)
    if validation["valid"]:
        registry.ingest(records)
    return {"filename": filename, "validation": validation, "statistics": registry.statistics(), "decision_counts": _decision_counts()}


@router.get("/reviews")
def reviews(page: int = 1, page_size: int = 8, search: str = "", status: str = "PENDING") -> dict[str, Any]:
    items = list(registry.review.items.values())
    if status != "ALL": items = [item for item in items if item.status == status]
    if search:
        query = search.casefold()
        items = [item for item in items if query in f"{item.left_id} {item.right_id} {item.review_id}".casefold()]
    total = len(items); start = max(0, page - 1) * page_size
    return {"items": [_record(item) for item in items[start:start + page_size]], "page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)}


@router.post("/reviews/{review_id}/decision")
def decide_review(review_id: str, decision: ReviewDecision) -> dict[str, Any]:
    try: return _record(registry.decide_review(review_id, decision.action, decision.reviewer, decision.explanation, decision.target_cnmc_id))
    except (KeyError, ValueError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/canonicals")
def canonicals(search: str = "") -> dict[str, Any]:
    values = registry.search(search) if search else registry.list_canonicals()
    return {"items": [_record(item) for item in values]}


@router.get("/mappings")
def mappings() -> dict[str, Any]:
    return {"items": [_record(item) for item in registry.mapping_history]}


@router.get("/benchmark")
def benchmark() -> dict[str, Any]:
    result = run_benchmark(generate_dataset(size=10_000))
    return result.as_dict()


@router.get("/demo")
def demo() -> dict[str, Any]:
    if not registry.records: registry.ingest(generate_dataset(size=24))
    return {"statistics": registry.statistics(), "decision_counts": _decision_counts(), "reviews": reviews(page_size=6), "canonicals": canonicals(), "mappings": mappings()}


@router.get("/health")
def materials_health() -> dict[str, str]:
    return {"status": "operational", "service": "material-registry"}


@router.get("/candidate/{review_id}")
def candidate(review_id: str) -> dict[str, Any]:
    item = registry.review.items.get(review_id)
    if not item: raise HTTPException(status_code=404, detail="Review candidate not found")
    left = registry.records.get(item.left_id, {}); right = registry.records.get(item.right_id, {})
    conflicts = []
    for key in set(left.get("extracted_attributes", {})) | set(right.get("extracted_attributes", {})):
        if left.get("extracted_attributes", {}).get(key) != right.get("extracted_attributes", {}).get(key): conflicts.append({"attribute": key, "left": left.get("extracted_attributes", {}).get(key), "right": right.get("extracted_attributes", {}).get(key)})
    return {"review": _record(item), "left": left, "right": right, "conflicts": conflicts}
