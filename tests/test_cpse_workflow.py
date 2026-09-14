import csv
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.materials import _validation
from app.api.routes import materials as materials_route
from app.benchmark.dataset import generate_dataset
from app.product import MaterialRegistry
from app.main import app


def test_cpse_fixture_contains_source_provenance_columns():
    record = generate_dataset(1, seed=3)[0]
    assert {
        "source_material_code",
        "enterprise",
        "plant",
        "material_group",
        "base_unit",
    } <= set(record)


def test_a_to_h_fixtures_have_stable_cpse_contract():
    required = {
        "record_id", "cpse_organization", "source_organization",
        "material_code", "original_description", "attributes",
        "ground_truth_group", "variant",
    }
    for letter in "ABCDEFGH":
        path = Path("data/test") / f"dataset_{letter}.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert required <= set(reader.fieldnames or [])
            first = next(reader)
            assert first["record_id"] and first["original_description"]


def test_canonical_and_mapping_metadata_expose_provenance():
    registry = MaterialRegistry()
    registry.ingest([
        {
            "record_id": "erp-1",
            "source": "erp",
            "material_code": "00042",
            "description": "steel bolt 10 mm",
        },
        {
            "record_id": "catalogue-1",
            "source": "catalogue",
            "material_code": "B-42",
            "description": "steel bolt 10 mm",
        },
    ])

    canonical = registry.list_canonicals()[0]
    assert canonical.metadata["member_count"] == 2
    assert canonical.metadata["source_systems"] == ["catalogue", "erp"]
    assert canonical.record["canonical_description"] == "steel bolt 10 mm"
    assert registry.mapping_history[0].source_description
    assert registry.mapping_history[0].metadata["record_id"]


def test_upload_validation_reports_structured_quality_issues():
    result = _validation([
        {"record_id": "1", "description": ""},
        {"record_id": "1", "description": ""},
    ])
    assert result["valid"] is False
    assert {issue["code"] for issue in result["issues"]} == {
        "missing_description",
        "duplicate_row",
    }


def test_actual_10k_cpse_upload_accounts_rows_and_mappings():
    fixture = Path("data/test/dataset_H.csv")
    payload = fixture.read_bytes()
    previous = materials_route.registry
    materials_route.registry = MaterialRegistry()
    try:
        response = TestClient(app).post(
            "/api/materials/upload",
            files={"file": ("dataset_H.csv", BytesIO(payload), "text/csv")},
        )
    finally:
        materials_route.registry = previous
    assert response.status_code == 200
    body = response.json()
    assert body["validation"]["rows"] == 10_000
    assert body["validation"]["valid"] is True
    assert body["statistics"]["records"] == 10_000
    assert body["statistics"]["mappings"] == 10_000
