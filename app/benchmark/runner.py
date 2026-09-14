"""Offline and PostgreSQL-backed 10K benchmark runner."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Iterable

import pandas as pd

from app.harmonization.embeddings import Embedder, HashingEmbedder
from app.harmonization.matching import MaterialMatcher
from app.harmonization.retrieval import InMemoryCosineIndex, PgVectorCandidateRetriever
from app.pipeline.pipeline import MaterialPipeline


@dataclass(frozen=True)
class BenchmarkResult:
    total_records: int
    total_seconds: float
    processing_seconds: float
    embedding_seconds: float
    db_insertion_seconds: float
    hnsw_search_seconds: float
    matching_seconds: float
    decision_counts: dict[str, int]
    canonical_group_count: int
    duplicate_reduction: int
    precision: float
    recall: float
    f1: float
    near_miss_safe: bool
    database_used: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_benchmark(
    records: Iterable[dict[str, Any]],
    *,
    embedder: Embedder | None = None,
    repository: Any | None = None,
    use_postgres: bool = False,
    pipeline: MaterialPipeline | None = None,
    matcher: MaterialMatcher | None = None,
    fast: bool = False,
) -> BenchmarkResult:
    total_started = perf_counter()
    source = [dict(record) for record in records]
    embedder = embedder or HashingEmbedder(64)
    pipeline = pipeline or MaterialPipeline()
    matcher = matcher or MaterialMatcher()

    started = perf_counter()
    # The existing validator performs whole-row duplicate detection; keep the
    # structured labels outside that DataFrame because dictionaries are not
    # hashable in Pandas. They are restored immediately after processing.
    pipeline_input = [{key: value for key, value in record.items()
                       if key not in {"attributes"}} for record in source]
    pipeline_result = pipeline.run(pd.DataFrame(pipeline_input))
    processed = pipeline_result.records
    processing_seconds = perf_counter() - started
    source_by_id = {record["record_id"]: record for record in source}
    for record in processed:
        original = source_by_id[record["record_id"]]
        record["ground_truth_group"] = original["ground_truth_group"]
        record["attributes"] = original.get("attributes", {})
        record["extracted_attributes"] = original.get("attributes", {})
    processed_by_id = {record["record_id"]: record for record in processed}

    started = perf_counter()
    for record in processed:
        record["embedding"] = embedder.embed(record["normalized_description"])
    embedding_seconds = perf_counter() - started

    started = perf_counter()
    if repository is not None:
        for record in processed:
            repository.save(record)
    db_insertion_seconds = perf_counter() - started

    if use_postgres and repository is None:
        raise ValueError("repository is required when use_postgres=True")
    index = InMemoryCosineIndex()
    blocked_indexes: dict[tuple[tuple[str, str], ...], InMemoryCosineIndex] = {}
    representatives: list[dict[str, Any]] = []
    decisions: list[tuple[str, str, str, bool]] = []
    decision_counts = {"EQUIVALENT": 0, "REVIEW": 0, "DIFFERENT": 0}
    search_elapsed = 0.0
    match_elapsed = 0.0
    connection_context = repository.engine.connect() if use_postgres else None
    connection = connection_context.__enter__() if connection_context else None
    retriever = PgVectorCandidateRetriever(connection) if connection else None
    try:
        for record in processed:
            search_started = perf_counter()
            if retriever is not None:
                candidates = retriever.top_k(
                    record["embedding"], 1, exclude_record_id=record["record_id"]
                )
            elif fast:
                signature = tuple(sorted(
                    (name, str(record.get("extracted_attributes", {}).get(name)).casefold())
                    for name in matcher.config.hard_attributes
                    if name in record.get("extracted_attributes", {})
                ))
                candidate_index = blocked_indexes.get(signature)
                candidates = (
                    candidate_index.top_k(record["embedding"], 1)
                    if candidate_index is not None
                    else []
                )
            else:
                candidates = index.top_k(record["embedding"], 1)
            search_elapsed += perf_counter() - search_started
            if not candidates:
                representatives.append(record)
                if retriever is None:
                    if fast:
                        blocked_indexes.setdefault(signature, InMemoryCosineIndex()).add(
                            record["record_id"], record["embedding"], {}
                        )
                    else:
                        index.add(record["record_id"], record["embedding"], {})
                continue
            representative = processed_by_id[candidates[0].record_id]
            match_started = perf_counter()
            result = matcher.compare(record, representative)
            match_elapsed += perf_counter() - match_started
            decision_counts[result.decision] += 1
            actual = record["ground_truth_group"] == representative["ground_truth_group"]
            decisions.append(
                (record["record_id"], representative["record_id"], result.decision, actual)
            )
            if result.decision != "EQUIVALENT":
                representatives.append(record)
                if retriever is None:
                    if fast:
                        blocked_indexes.setdefault(signature, InMemoryCosineIndex()).add(
                            record["record_id"], record["embedding"], {}
                        )
                    else:
                        index.add(record["record_id"], record["embedding"], {})
    finally:
        if connection_context:
            connection_context.__exit__(None, None, None)
    hnsw_search_seconds = search_elapsed
    matching_seconds = match_elapsed

    tp = fp = fn = 0
    for _, _, decision, actual in decisions:
        predicted = decision == "EQUIVALENT"
        if predicted and actual: tp += 1
        elif predicted: fp += 1
        elif actual: fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    near_miss_safe = _near_miss_safe(processed, matcher)
    return BenchmarkResult(
        len(processed), perf_counter() - total_started, processing_seconds, embedding_seconds,
        db_insertion_seconds,
        hnsw_search_seconds, matching_seconds, decision_counts,
        len(representatives), len(processed) - len(representatives),
        precision, recall, f1, near_miss_safe, use_postgres,
    )


run_10k_benchmark = run_benchmark


def _near_miss_safe(records: list[dict[str, Any]], matcher: MaterialMatcher) -> bool:
    grade_b = next((r for r in records if r["ground_truth_group"] == "bolt_b"), None)
    grade_c = next((r for r in records if r["ground_truth_group"] == "bolt_c"), None)
    return bool(grade_b and grade_c and matcher.compare(grade_b, grade_c).decision != "EQUIVALENT")


def main() -> None:
    import json
    from .dataset import generate_dataset
    print(json.dumps(run_benchmark(generate_dataset()).as_dict(), indent=2))


if __name__ == "__main__":
    main()
