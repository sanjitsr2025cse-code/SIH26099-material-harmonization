from app.harmonization.embeddings import HashingEmbedder, SentenceTransformerEmbedder
from app.harmonization.matching import MaterialMatcher, MatchConfig
from app.harmonization.multilingual import MultilingualProcessor
from app.harmonization.retrieval import InMemoryCosineIndex
from app.harmonization.service import harmonize_records

def test_multilingual_processing_preserves_original_and_script():
    result = MultilingualProcessor().process("  Acero inoxidable １０ mm  ")
    assert result.original.startswith("  ")
    assert result.language == "en"
    assert "10 mm" in result.normalized

def test_hash_embeddings_are_deterministic_and_retrievable():
    embedder = HashingEmbedder(32)
    first, second = embedder.embed("stainless steel bolt"), embedder.embed("stainless steel bolt")
    assert first == second
    index = InMemoryCosineIndex()
    index.add("a", first, {"source": "test"})
    assert index.top_k(first, 1)[0].record_id == "a"

def test_injected_sentence_model_and_fallback():
    class FakeModel:
        def encode(self, text, normalize_embeddings=True):
            return [1, 0, 0]
    embedder = SentenceTransformerEmbedder(fallback=HashingEmbedder(8))
    embedder._model = FakeModel()
    assert embedder.embed("bolt") == [1.0, 0.0, 0.0]

def test_hard_conflict_and_confidence_decisions():
    matcher = MaterialMatcher(MatchConfig(equivalent_threshold=.7, review_threshold=.3))
    same = {"normalized_description": "steel bolt", "embedding": [1, 0], "attributes": {"grade": "304", "size": "10"}}
    assert matcher.compare(same, same).decision == "EQUIVALENT"
    different = dict(same, attributes={"grade": "316", "size": "10"})
    result = matcher.compare(same, different)
    assert result.decision == "DIFFERENT"
    assert "grade" in result.reasons[0]

def test_end_to_end_sample_records_preserve_source_and_attributes():
    records = harmonize_records([
        {"record_id": "1", "description": "Stainless bolt 10 mm", "attributes": {"size": "10"}}
    ])
    assert records[0]["original_description"] == "Stainless bolt 10 mm"
    assert records[0]["extracted_attributes"] == {"size": "10"}
    assert len(records[0]["embedding"]) > 0
