"""Lazy optional sentence-transformer embeddings and a deterministic fallback."""
from dataclasses import dataclass, field
import hashlib
import math
import re
from typing import Any, Protocol

from app.harmonization.config import HarmonizationSettings

@dataclass
class EmbeddingRecord:
    record_id: str
    vector: list[float]
    model: str = "hashing-v1"
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def embedding(self) -> list[float]:
        return self.vector

class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...

class HashingEmbedder:
    def __init__(self, dimensions: int = 256):
        if dimensions < 8:
            raise ValueError("dimensions must be at least 8")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
        for token in tokens or [""]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def record(self, record_id: str, text: str, metadata: dict[str, Any] | None = None) -> EmbeddingRecord:
        return EmbeddingRecord(record_id, self.embed(text), "hashing-v1", text, metadata or {})

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

class SentenceTransformerEmbedder:
    """Model is imported and loaded only when the first embedding is requested."""
    def __init__(self, model_name: str | None = None,
                 fallback: Embedder | None = None):
        self.model_name = model_name or HarmonizationSettings.from_env().embedding_model
        self.fallback = fallback or HashingEmbedder()
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except (ImportError, OSError, RuntimeError):
                self._model = False
        return self._model

    def embed(self, text: str) -> list[float]:
        model = self._load()
        if model is False:
            return self.fallback.embed(text)
        values = model.encode(text, normalize_embeddings=True)
        return [float(value) for value in values]

    def record(self, record_id: str, text: str, metadata: dict[str, Any] | None = None) -> EmbeddingRecord:
        model = self._load()
        name = self.model_name if model is not False else "hashing-v1"
        return EmbeddingRecord(record_id, self.embed(text), name, text, metadata or {})

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
