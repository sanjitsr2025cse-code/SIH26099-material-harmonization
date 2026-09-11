from app.benchmark import generate_dataset, run_benchmark
from app.harmonization.embeddings import HashingEmbedder
from unittest.mock import patch


def test_generator_is_deterministic_and_covers_variations():
    first = generate_dataset(10_000, seed=7)
    second = generate_dataset(10_000, seed=7)
    assert first == second
    assert len(first) == 10_000
    assert {item["variant"] for item in first} >= {
        "exact", "near_duplicate", "abbreviation", "multilingual",
        "unit_format", "terminology", "unrelated",
    }
    assert all("ground_truth_group" in item for item in first)


def test_benchmark_result_shape_is_offline_and_deterministic():
    result = run_benchmark(generate_dataset(120, seed=3), embedder=HashingEmbedder(32))
    payload = result.as_dict()
    assert payload["total_records"] == 120
    assert set(payload["decision_counts"]) == {"EQUIVALENT", "REVIEW", "DIFFERENT"}
    assert payload["canonical_group_count"] > 0
    assert payload["duplicate_reduction"] >= 0
    for key in ("processing_seconds", "embedding_seconds", "db_insertion_seconds",
                "hnsw_search_seconds", "matching_seconds", "total_seconds",
                "precision", "recall", "f1"):
        assert payload[key] >= 0
    assert payload["database_used"] is False


def test_grade_b_and_grade_c_near_miss_is_not_merged():
    records = generate_dataset(200, seed=1)
    result = run_benchmark(records, embedder=HashingEmbedder(32))
    assert result.near_miss_safe


def test_postgres_mode_wires_repository_and_pgvector_retriever():
    class ConnectionContext:
        def __enter__(self):
            return object()

        def __exit__(self, *_):
            return False

    class Repository:
        def __init__(self):
            self.saved = []
            self.engine = type("Engine", (), {"connect": lambda self: ConnectionContext()})()

        def save(self, record):
            self.saved.append(record)

    class Retriever:
        calls = 0

        def __init__(self, connection):
            assert connection is not None

        def top_k(self, vector, k, exclude_record_id=None):
            type(self).calls += 1
            return []

    repository = Repository()
    retriever = Retriever
    with patch("app.benchmark.runner.PgVectorCandidateRetriever", retriever):
        result = run_benchmark(
            generate_dataset(8, seed=4),
            embedder=HashingEmbedder(16),
            repository=repository,
            use_postgres=True,
        )

    assert len(repository.saved) == 8
    assert retriever.calls == 8
    assert result.database_used is True
    assert result.db_insertion_seconds >= 0
    assert result.hnsw_search_seconds >= 0
    assert result.total_seconds >= result.processing_seconds
