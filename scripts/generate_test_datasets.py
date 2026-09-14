"""Generate deterministic CPSE workflow fixtures A-H under data/test."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.benchmark.dataset import generate_dataset

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "test"
FIELDS = [
    "record_id", "cpse_organization", "source_organization", "material_code",
    "original_description", "attributes", "ground_truth_group", "variant",
]


def _records(size: int, seed: int, variant: str | None = None) -> list[dict[str, object]]:
    result = []
    for item in generate_dataset(size=size, seed=seed):
        value = {
            "record_id": item["record_id"],
            "cpse_organization": item["enterprise"],
            "source_organization": item["source"],
            "material_code": item["material_code"],
            "original_description": item["original_description"],
            "attributes": item["attributes"],
            "ground_truth_group": item["ground_truth_group"],
            "variant": variant or item["variant"],
        }
        result.append(value)
    return result


def write_dataset(letter: str, records: list[dict[str, object]]) -> None:
    path = OUT / f"dataset_{letter}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["attributes"] = json.dumps(row["attributes"], sort_keys=True)
            writer.writerow(row)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_dataset("A", _records(48, 101))
    write_dataset("B", _records(48, 102, "near_duplicate"))
    write_dataset("C", _records(48, 103, "multilingual"))
    write_dataset("D", _records(48, 104, "abbreviation"))
    write_dataset("E", _records(48, 105, "unit_format"))
    write_dataset("F", _records(48, 106, "terminology"))
    write_dataset("G", _records(48, 107, "unrelated"))
    write_dataset("H", _records(10_000, 108))


if __name__ == "__main__":
    main()
