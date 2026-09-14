"""Export the deterministic benchmark dataset as a CSV file."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.benchmark.dataset import generate_dataset


OUTPUT = Path(__file__).resolve().parents[1] / "data" / "materials_10k.csv"


def export_dataset(output: Path = OUTPUT, size: int = 10_000) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    records = generate_dataset(size=size)
    fieldnames = [
        "record_id",
        "source",
        "material_code",
        "description",
        "attributes",
        "ground_truth_group",
        "variant",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {key: record[key] for key in fieldnames}
            row["attributes"] = json.dumps(row["attributes"], ensure_ascii=False, sort_keys=True)
            writer.writerow(row)
    return output


if __name__ == "__main__":
    print(export_dataset())
