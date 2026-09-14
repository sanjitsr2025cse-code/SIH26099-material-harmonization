"""Deterministic synthetic CPSE material data used by validation benchmarks."""
from __future__ import annotations

import csv
import io
import json
import random
from typing import Any

_FAMILIES = (
    ("bolt_b", "STEEL BOLT M10 GRADE B", {"grade": "B", "size": "M10", "standard": "ISO 4014"}),
    ("bolt_c", "STEEL BOLT M10 GRADE C", {"grade": "C", "size": "M10", "standard": "ISO 4014"}),
    ("bolt_m12", "STEEL BOLT M12 GRADE B", {"grade": "B", "size": "M12", "standard": "ISO 4014"}),
    ("nut_m10", "STEEL HEX NUT M10 GRADE B", {"grade": "B", "size": "M10", "standard": "ISO 4032"}),
    ("washer", "STEEL WASHER M10", {"size": "M10", "standard": "ISO 7089"}),
    ("pipe", "CARBON STEEL PIPE 50 MM SCH 40", {"size": "50 mm", "standard": "ASTM A106"}),
    ("valve", "GATE VALVE 50 MM 150 PSI", {"size": "50 mm", "pressure": "150 psi", "standard": "API 600"}),
    ("cable", "POWER CABLE 4 CORE 240 V", {"size": "4 core", "voltage": "240 V"}),
    ("bearing", "DEEP GROOVE BALL BEARING 6205", {"size": "6205", "standard": "ISO 15"}),
    ("flange", "WELD NECK FLANGE DN50 PN16", {"size": "DN50", "pressure": "PN16", "standard": "EN 1092"}),
    ("gasket", "SPIRAL WOUND GASKET DN50", {"size": "DN50", "standard": "ASME B16.20"}),
    ("motor", "INDUCTION MOTOR 5 KW 415 V", {"size": "5 kW", "voltage": "415 V"}),
)

_ABBREVIATIONS = {"STEEL": "STL", "BOLT": "BLT", "GRADE": "GR", "PRESSURE": "P", "VOLTAGE": "V"}
_TRANSLATIONS = {
    "bolt_b": "БОЛТ СТАЛЬ M10 КЛАСС B",
    "bolt_c": "БОЛТ СТАЛЬ M10 КЛАСС C",
    "pipe": "TUBO ACERO CARBONO 50 MM SCH 40",
    "valve": "VÁLVULA COMPUERTA 50 MM 150 PSI",
    "cable": "CÂBLE PUISSANCE 4 ÂMES 240 V",
}
_CPSE_NAMES = (
    "NTPC", "BHEL", "IOCL", "ONGC", "GAIL",
    "SAIL", "Coal India", "Power Grid", "BPCL", "HPCL",
)


def generate_dataset(size: int = 10_000, seed: int = 10_000) -> list[dict[str, Any]]:
    """Return a reproducible CPSE-like dataset with labels for evaluation.

    ``ground_truth_group`` is intentionally retained in the generated records,
    but is not consumed by the matching pipeline.
    """
    if size < 1:
        raise ValueError("size must be positive")
    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    equivalent_groups = min(2_000, size // 5)
    near_miss_groups = min(250, max(0, (size - equivalent_groups * 4) // 2))
    singleton_count = size - equivalent_groups * 4 - near_miss_groups * 2
    record_number = 0

    def add_record(
        group_id: str,
        description: str,
        attrs: dict[str, str],
        variant: str,
        cpse_index: int,
    ) -> None:
        nonlocal record_number
        record_number += 1
        cpse = _CPSE_NAMES[cpse_index % len(_CPSE_NAMES)]
        material_code = f"{cpse[:3].upper()}-{group_id.upper()}-{record_number:05d}"
        records.append({
            "record_id": f"cpse-{record_number:05d}",
            "source": ("erp", "catalogue", "maintenance")[record_number % 3],
            "material_code": material_code,
            "source_material_code": material_code,
            "enterprise": cpse,
            "plant": f"PLANT-{record_number % 12 + 1:02d}",
            "material_group": group_id,
            "base_unit": "EA",
            "description": description,
            "original_description": description,
            "attributes": dict(attrs),
            "ground_truth_group": group_id,
            "variant": variant,
        })

    # Four different CPSE local identities intentionally describe each
    # equivalent material. The shared item token keeps distinct groups apart
    # while allowing terminology and formatting variations to match.
    for group_number in range(equivalent_groups):
        family_id, canonical, attrs = _FAMILIES[group_number % len(_FAMILIES)]
        group_id = f"equivalent_{group_number:04d}"
        attrs = dict(attrs)
        attrs["standard"] = f"{attrs.get('standard', 'CPSE')}-{group_number:04d}"
        item_token = f"ITEM {group_number:04d}"
        multilingual_description = (
            f"{canonical} बोल्ट ITEM {group_number:04d}"
            if group_number % 5 == 0
            else f"{canonical.replace('50 MM', '50mm').replace('M10', '10 mm').replace('240 V', '240VAC')} {item_token}"
        )
        descriptions = (
            f"{canonical} {item_token}",
            f"{canonical.replace('GRADE', 'GR')} {item_token}",
            f"{item_token} {canonical.replace('BOLT', 'HEX BOLT')}",
            multilingual_description,
        )
        variants = ("exact", "abbreviation", "terminology",
                    "multilingual" if group_number % 5 == 0 else "unit_format")
        for member, (description, variant) in enumerate(zip(descriptions, variants)):
            add_record(group_id, description, attrs, variant, group_number * 4 + member)

    # Hard-attribute near misses use almost identical text but intentionally
    # conflicting Grade, Voltage, Pressure, or Size values.
    near_miss_specs = (
        ("STEEL BOLT M10 GRADE B", {"grade": "B", "size": "M10", "standard": "ISO 4014"},
         "STEEL BOLT M10 GRADE C", {"grade": "C", "size": "M10", "standard": "ISO 4014"}),
        ("POWER CABLE 4 CORE 240 V", {"size": "4 core", "voltage": "240 V"},
         "POWER CABLE 4 CORE 415 V", {"size": "4 core", "voltage": "415 V"}),
        ("WELD NECK FLANGE DN50 PN16", {"size": "DN50", "pressure": "PN16", "standard": "EN 1092"},
         "WELD NECK FLANGE DN50 PN40", {"size": "DN50", "pressure": "PN40", "standard": "EN 1092"}),
        ("CARBON STEEL PIPE 10 MM SCH 40", {"size": "10 mm", "standard": "ASTM A106"},
         "CARBON STEEL PIPE 12 MM SCH 40", {"size": "12 mm", "standard": "ASTM A106"}),
    )
    for group_number in range(near_miss_groups):
        spec = near_miss_specs[group_number % len(near_miss_specs)]
        for side in range(2):
            description, attrs = spec[side * 2], spec[side * 2 + 1]
            group_id = (
                ("bolt_b" if side == 0 else "bolt_c")
                if group_number == 0
                else f"near_miss_{group_number:04d}_{'a' if side == 0 else 'b'}"
            )
            add_record(
                group_id,
                f"{description} ITEM NM{group_number:04d}",
                attrs,
                "near_duplicate",
                equivalent_groups * 4 + group_number * 2 + side,
            )

    # Singleton records remain genuinely unique and are not forced into any
    # existing canonical group.
    for singleton_number in range(singleton_count):
        group_id = f"singleton_{singleton_number:04d}"
        description = f"UNIQUE CPSE MATERIAL {singleton_number:04d} CERAMIC LINER"
        add_record(
            group_id,
            description,
            {"size": f"{1000 + singleton_number} mm", "standard": "CPSE-OTHER"},
            "unrelated",
            equivalent_groups * 4 + near_miss_groups * 2 + singleton_number,
        )
    rng.shuffle(records)
    return records


# Descriptive alias for callers that want to make the synthetic nature clear.
generate_synthetic_dataset = generate_dataset


def demo_dataset_csv(size: int = 10_000, seed: int = 10_000) -> bytes:
    """Return the deterministic benchmark dataset in the legacy CSV format.

    This compatibility helper preserves the existing generated records and
    serializes only the attributes field for CSV transport.
    """
    fieldnames = [
        "record_id",
        "source",
        "material_code",
        "source_material_code",
        "enterprise",
        "plant",
        "material_group",
        "base_unit",
        "description",
        "attributes",
        "ground_truth_group",
        "variant",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record in generate_dataset(size=size, seed=seed):
        row = {key: record[key] for key in fieldnames}
        row["attributes"] = json.dumps(row["attributes"], ensure_ascii=False, sort_keys=True)
        writer.writerow(row)
    return output.getvalue().encode("utf-8")
