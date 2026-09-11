"""Run the 10K validation benchmark offline or against PostgreSQL/pgvector."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.benchmark.dataset import generate_dataset
from app.benchmark.runner import run_benchmark

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--postgres", action="store_true",
                        help="Use DATABASE_URL, MaterialRepository, and pgvector/HNSW retrieval")
    parser.add_argument("--size", type=int, default=10_000)
    args = parser.parse_args()

    repository = None
    embedder = None
    if args.postgres:
        from app.harmonization.embeddings import HashingEmbedder
        from app.harmonization.persistence import MaterialRepository

        repository = MaterialRepository()
        repository.create_schema()
        # Keep the benchmark reproducible and fast; production model validation
        # is covered by the separate real-model smoke test.
        embedder = HashingEmbedder(384)

    result = run_benchmark(
        generate_dataset(args.size),
        embedder=embedder,
        repository=repository,
        use_postgres=args.postgres,
    )
    print(json.dumps(result.as_dict(), indent=2))

    if repository is not None:
        from sqlalchemy import text

        with repository.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM material_embeddings WHERE record_id LIKE 'cpse-%'")
            )
