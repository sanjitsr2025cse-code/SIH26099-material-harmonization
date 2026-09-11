"""Top-k vector retrieval adapters."""
from dataclasses import dataclass, field
import math
import re
from typing import Any, Sequence

@dataclass
class Candidate:
    record_id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(x*x for x in left)) * math.sqrt(sum(y*y for y in right))
    return sum(x*y for x, y in zip(left, right)) / denominator if denominator else 0.0

class InMemoryCosineIndex:
    def __init__(self):
        self._items: dict[str, tuple[list[float], dict[str, Any]]] = {}

    def add(self, record_id: str, vector: Sequence[float] | None = None,
            metadata: dict[str, Any] | None = None):
        if vector is None and hasattr(record_id, "record_id"):
            record = record_id
            record_id, vector, metadata = record.record_id, record.vector, record.metadata
        if vector is None:
            raise ValueError("vector is required")
        self._items[record_id] = (list(vector), metadata or {})

    def top_k(self, vector: Sequence[float], k: int = 5) -> list[Candidate]:
        if k <= 0:
            return []
        return [Candidate(record_id, score, metadata)
                for record_id, (candidate, metadata), score in
                sorted(((rid, item, cosine_similarity(vector, item[0]))
                        for rid, item in self._items.items()),
                       key=lambda entry: entry[2], reverse=True)[:k]]

    query = top_k

class PgVectorCandidateRetriever:
    """Uses an injected SQLAlchemy connection; never opens a DB during import."""
    def __init__(self, connection, table: str = "material_embeddings"):
        self.connection, self.table = connection, table

    def top_k(self, vector: Sequence[float], k: int = 5) -> list[Candidate]:
        query = (f"SELECT record_id, 1 - (embedding <=> :vector) AS score, metadata "
                 f"FROM {self.table} ORDER BY embedding <=> :vector LIMIT :limit")
        from sqlalchemy import text

        rows = self.connection.execute(
            text(query), {"vector": str(list(vector)), "limit": k}
        )
        return [Candidate(row[0], float(row[1]), row[2] or {}) for row in rows]

def hnsw_index_sql(table: str = "material_embeddings", column: str = "embedding") -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*", column
    ):
        raise ValueError("table and column must be simple SQL identifiers")
    return (f"CREATE INDEX IF NOT EXISTS {table}_{column}_hnsw "
            f"ON {table} USING hnsw ({column} vector_cosine_ops);")
