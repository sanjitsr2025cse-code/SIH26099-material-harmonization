from app.product import MaterialRegistry, evaluate_decisions
from app.product.dashboard import demo_dataset_csv
import pandas as pd
from io import BytesIO


def test_registry_clusters_deterministically_and_tracks_mappings():
    registry = MaterialRegistry()
    registry.ingest([
        {"record_id": "z", "source": "erp", "material_code": "Z",
         "description": "steel bolt 10 mm"},
        {"record_id": "a", "source": "catalogue", "material_code": "A",
         "description": "steel bolt 10 mm"},
        {"record_id": "different", "source": "erp", "material_code": "D",
         "description": "steel bolt 20 mm", "attributes": {"size": "20"}},
    ])
    canonicals = registry.list_canonicals()
    assert canonicals[0].cnmc_id == "CNMC-000001"
    assert canonicals[0].member_ids == ("a", "z")
    assert len(registry.mapping_history) == 3
    assert registry.statistics()["canonical_materials"] == 2


def test_review_approval_preserves_human_decision():
    registry = MaterialRegistry()
    registry.matcher.config.equivalent_threshold = 1.1
    registry.matcher.config.review_threshold = 0.0
    registry.ingest([
        {"record_id": "a", "description": "brass valve"},
        {"record_id": "b", "description": "brass valve"},
    ])
    item = registry.candidates()[0]
    registry.decide_review(item.review_id, "approve", "reviewer", "same item")
    assert item.human_decision.explanation == "same item"
    assert len(registry.list_canonicals()) == 1


def test_evaluation_reports_error_metrics():
    registry = MaterialRegistry()
    registry.matcher.config.equivalent_threshold = 1.1
    registry.matcher.config.review_threshold = 0.0
    registry.ingest([
        {"record_id": "a", "description": "bolt"},
        {"record_id": "b", "description": "nut"},
    ])
    metrics = evaluate_decisions(registry.decisions, {("a", "b"): True})
    assert metrics.false_negatives == 1
    assert metrics.recall == 0.0


def test_demo_dataset_csv_uses_shared_generator():
    payload = demo_dataset_csv(100, seed=7)
    frame = pd.read_csv(BytesIO(payload))
    assert len(frame) == 100
    assert {"record_id", "description", "ground_truth_group"} <= set(frame.columns)
