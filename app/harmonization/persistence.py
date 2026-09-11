"""Optional PostgreSQL/pgvector persistence, configured entirely by environment."""
from typing import Any

from app.harmonization.config import HarmonizationSettings


def database_url() -> str:
    return HarmonizationSettings.from_env().database_url

SCHEMA_SQL = """CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS material_embeddings (
 record_id TEXT PRIMARY KEY, original_description TEXT NOT NULL,
 normalized_description TEXT NOT NULL, extracted_attributes JSONB NOT NULL DEFAULT '{}',
 embedding vector, metadata JSONB NOT NULL DEFAULT '{}');
"""

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
            for statement in SCHEMA_SQL.split(";"):
                if statement.strip():
                    connection.exec_driver_sql(statement)

    def save(self, record: dict[str, Any]):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO material_embeddings (record_id, original_description, normalized_description, extracted_attributes, embedding, metadata) "
                "VALUES (:id,:original,:normalized,:attrs,:embedding,:metadata) ON CONFLICT (record_id) DO UPDATE SET normalized_description=:normalized",
                {"id": record["record_id"], "original": record.get("original_description", ""),
                 "normalized": record.get("normalized_description", ""), "attrs": str(record.get("extracted_attributes", {})),
                 "embedding": str(record.get("embedding", [])), "metadata": str(record.get("metadata", {}))})
