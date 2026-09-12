import csv
import runpy


def test_export_script_writes_benchmark_fields(tmp_path):
    module = runpy.run_path("scripts/export_materials_10k.py")
    output = module["export_dataset"](tmp_path / "materials.csv", size=5)

    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 5
    assert {
        "record_id",
        "source",
        "material_code",
        "description",
        "attributes",
        "ground_truth_group",
        "variant",
    } == set(rows[0])
