"""Optional PostgreSQL/pgvector persistence, configured entirely by environment."""
import json
import re
from typing import Any

from app.harmonization.config import HarmonizationSettings


def database_url() -> str:
    value = HarmonizationSettings.from_env().database_url
    if not value:
        raise RuntimeError(
            "DATABASE_URL is required for PostgreSQL persistence; "
            "set it in an untracked .env file."
        )
    return value

def schema_sql(dimensions: int = 384) -> str:
    if dimensions < 1:
        raise ValueError("embedding dimensions must be positive")
    return f"""CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS material_embeddings (
 record_id TEXT PRIMARY KEY, original_description TEXT NOT NULL,
 normalized_description TEXT NOT NULL, extracted_attributes JSONB NOT NULL DEFAULT '{{}}',
 embedding vector({dimensions}) NOT NULL, metadata JSONB NOT NULL DEFAULT '{{}}');
"""


SCHEMA_SQL = schema_sql()


def _vector_literal(values: list[float]) -> str:
    if not values:
        raise ValueError("embedding must not be empty")
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def _json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _safe_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return value

def setup_hnsw_sql(table: str = "material_embeddings", column: str = "embedding") -> str:
    from app.harmonization.retrieval import hnsw_index_sql
    return hnsw_index_sql(table, column)

class MaterialRepository:
    def __init__(self, engine=None):
        if engine is None:
            try:
                from sqlalchemy import create_engine
            except ImportError as exc:
                raise RuntimeError("Install optional sqlalchemy and psycopg to use PostgreSQL") from exc
            engine = create_engine(database_url())
        self.engine = engine

    def create_schema(self):
        with self.engine.begin() as connection:
            schema = schema_sql(HarmonizationSettings.from_env().embedding_dimensions)
            for statement in schema.split(";"):
                if statement.strip():
                    connection.exec_driver_sql(statement)
            connection.exec_driver_sql(setup_hnsw_sql())

    def save(self, record: dict[str, Any]):
        embedding = record.get("embedding", [])
        if len(embedding) != HarmonizationSettings.from_env().embedding_dimensions:
            raise ValueError("embedding dimension does not match EMBEDDING_DIMENSIONS")
        from sqlalchemy import text

        with self.engine.begin() as connection:
            connection.execute(
                text(
                "INSERT INTO material_embeddings (record_id, original_description, normalized_description, extracted_attributes, embedding, metadata) "
                "VALUES (:id,:original,:normalized,:attrs,:embedding,:metadata) ON CONFLICT (record_id) DO UPDATE SET normalized_description=:normalized",
                ),
                {"id": record["record_id"], "original": record.get("original_description", ""),
                 "normalized": record.get("normalized_description", ""),
                 "attrs": _json_value(record.get("extracted_attributes", {})),
                 "embedding": _vector_literal(embedding),
                 "metadata": _json_value(record.get("metadata", {}))})
