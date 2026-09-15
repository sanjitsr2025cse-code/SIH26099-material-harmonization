"""Presentation adapters for the material harmonization registry."""
from __future__ import annotations

import io
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.benchmark.dataset import generate_dataset
from app.benchmark.runner import run_benchmark
from app.pipeline.attributes import prepare_records
from app.product.registry import MaterialRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/materials", tags=["materials"])
registry = MaterialRegistry()


# ---------------------------------------------------------------------------
# Startup helper — called from app.main on_event("startup")
# ---------------------------------------------------------------------------

def load_demo_data() -> None:
    """Populate the registry with a 2K demo dataset if it is empty."""
    if registry.records:
        return
    logger.info("Loading 2K demo dataset into registry…")
    dataset = generate_dataset(size=2_000, seed=10_000)
    registry.ingest(dataset)
    logger.info(
        "Demo dataset loaded: %d records, %d canonical materials, %d mappings",
        len(registry.records),
        len(registry.canonicals),
        len(registry.mapping_history),
    )


# ---------------------------------------------------------------------------
# Benchmark job management (async, non-blocking)
# ---------------------------------------------------------------------------

@dataclass
class _BenchmarkJob:
    job_id: str
    status: str  # queued | running | completed | failed
    dataset_size: int
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None


_benchmark_jobs: dict[str, _BenchmarkJob] = {}
_benchmark_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ReviewDecision(BaseModel):
    action: str = Field(pattern="^(APPROVE|REJECT|OVERRIDE)$")
    reviewer: str = Field(min_length=1)
    explanation: str = ""
    target_cnmc_id: str | None = None


class BenchmarkStartRequest(BaseModel):
    size: int = Field(default=2_000, ge=10, le=100_000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/overview")
def overview() -> dict[str, Any]:
    return {
        "statistics": registry.statistics(),
        "decision_counts": _decision_counts(),
        "cpse_coverage": registry.cpse_coverage(),
        "health": "operational",
    }


@router.post("/upload")
async def upload_materials(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or "upload.csv"
    payload = await file.read()
    try:
        import pandas as pd
        frame = pd.read_csv(io.BytesIO(payload)) if filename.lower().endswith(".csv") else pd.read_excel(io.BytesIO(payload))
        records = prepare_records(frame.to_dict("records"))
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
def canonicals(search: str = "", cpse: str = "", category: str = "",
               page: int = 1, page_size: int = 50) -> dict[str, Any]:
    """Return rich CNMC view models with source materials and CPSE provenance."""
    items = registry.cnmc_details()

    if search:
        query = search.casefold()
        items = [item for item in items
                 if query in item["cnmc_id"].casefold()
                 or query in item["canonical_description"].casefold()
                 or any(query in sm["material_code"].casefold()
                        or query in sm["original_description"].casefold()
                        for sm in item["source_materials"])]

    if cpse:
        items = [item for item in items if cpse in item["cpses"]]

    if category:
        cat_lower = category.casefold()
        items = [item for item in items
                 if item.get("category", "").casefold() == cat_lower]

    total = len(items)
    start = max(0, page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/mappings")
def mappings() -> dict[str, Any]:
    return {"items": [_record(item) for item in registry.mapping_history]}


# ---------------------------------------------------------------------------
# Benchmark — async job system
# ---------------------------------------------------------------------------

@router.post("/benchmark/start")
def start_benchmark(body: BenchmarkStartRequest | None = None) -> dict[str, Any]:
    """Start a benchmark run in the background. Returns a job_id for polling."""
    size = body.size if body else 2_000
    job_id = uuid.uuid4().hex[:8]
    job = _BenchmarkJob(job_id=job_id, status="queued", dataset_size=size)
    with _benchmark_lock:
        _benchmark_jobs[job_id] = job

    def _run() -> None:
        job.status = "running"
        job.started_at = time.time()
        try:
            dataset = generate_dataset(size=size)
            result = run_benchmark(dataset)
            job.result = result.as_dict()
            job.status = "completed"
        except Exception as exc:
            logger.exception("Benchmark job %s failed", job_id)
            job.error = str(exc)
            job.status = "failed"
        finally:
            job.completed_at = time.time()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"job_id": job_id, "status": "queued", "dataset_size": size}


@router.get("/benchmark/latest")
def benchmark_latest() -> dict[str, Any]:
    """Return the most recent completed benchmark result, if any."""
    with _benchmark_lock:
        completed = [j for j in _benchmark_jobs.values() if j.status == "completed"]
    if not completed:
        return {"status": "none", "result": None}
    latest = max(completed, key=lambda j: j.completed_at or 0)
    return {
        "job_id": latest.job_id,
        "status": latest.status,
        "dataset_size": latest.dataset_size,
        "result": latest.result,
        "completed_at": latest.completed_at,
    }


@router.get("/benchmark/{job_id}")
def benchmark_status(job_id: str) -> dict[str, Any]:
    """Poll for the status of a benchmark job."""
    with _benchmark_lock:
        job = _benchmark_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Benchmark job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "dataset_size": job.dataset_size,
        "result": job.result,
        "error": job.error,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


# ---------------------------------------------------------------------------
# Legacy / compatibility
# ---------------------------------------------------------------------------

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
