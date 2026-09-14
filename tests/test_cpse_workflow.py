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
        canonicals = TestClient(app).get("/api/materials/canonicals").json()["items"]
    finally:
        materials_route.registry = previous
    assert response.status_code == 200
    body = response.json()
    assert body["validation"]["rows"] == 10_000
    assert body["validation"]["valid"] is True
    assert body["statistics"]["records"] == 10_000
    assert body["statistics"]["mappings"] == 10_000
    assert 3_000 <= body["statistics"]["canonical_materials"] <= 4_000
    assert sum(len(item["member_ids"]) > 1 for item in canonicals) >= 1_900
    assert sum(
        len({
            record.get("enterprise", record.get("cpse_organization"))
            for record in item["source_records"]
        }) > 1
        for item in canonicals
    ) >= 1_900
    groups = {}
    for item in canonicals:
        for record in item["source_records"]:
            groups.setdefault(record["ground_truth_group"], set()).add(item["cnmc_id"])
    near_miss_groups = {
        group for group in groups if group.startswith("near_miss_")
    }
    assert near_miss_groups
    for group in near_miss_groups:
        assert len(groups[group]) == 1
    for group_number in range(250):
        left_key = "bolt_b" if group_number == 0 else f"near_miss_{group_number:04d}_a"
        right_key = "bolt_c" if group_number == 0 else f"near_miss_{group_number:04d}_b"
        left = groups[left_key]
        right = groups[right_key]
        assert left.isdisjoint(right)
