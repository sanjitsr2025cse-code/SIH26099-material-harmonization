"""Environment-backed settings for optional harmonization integrations."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HarmonizationSettings:
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    database_url: str = "postgresql+psycopg://localhost/materials"
    equivalent_threshold: float = 0.82
    review_threshold: float = 0.58
    retrieval_top_k: int = 5

    @classmethod
    def from_env(cls) -> "HarmonizationSettings":
        return cls(
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            equivalent_threshold=float(
                os.getenv("MATCH_EQUIVALENT_THRESHOLD", cls.equivalent_threshold)
            ),
            review_threshold=float(
                os.getenv("MATCH_REVIEW_THRESHOLD", cls.review_threshold)
            ),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", cls.retrieval_top_k)),
        )
