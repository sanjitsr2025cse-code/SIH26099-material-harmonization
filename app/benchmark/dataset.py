"""Deterministic synthetic CPSE material data used by validation benchmarks."""
from __future__ import annotations

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


def generate_dataset(size: int = 10_000, seed: int = 10_000) -> list[dict[str, Any]]:
    """Return a reproducible CPSE-like dataset with labels for evaluation.

    ``ground_truth_group`` is intentionally retained in the generated records,
    but is not consumed by the matching pipeline.
    """
    if size < 1:
        raise ValueError("size must be positive")
    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    for index in range(size):
        family_id, canonical, attrs = _FAMILIES[index % len(_FAMILIES)]
        variant = ("exact", "near_duplicate", "abbreviation", "multilingual",
                   "unit_format", "terminology", "unrelated")[index % 7]
        # A deterministic set of unrelated products exercises false-positive safety.
        if variant == "unrelated":
            unrelated_number = index // len(_FAMILIES)
            family_id = f"unrelated_{unrelated_number}"
            canonical = f"UNRELATED MATERIAL {unrelated_number} CERAMIC LINER"
            attrs = {"size": f"{100 + unrelated_number} mm", "standard": "CPSE-OTHER"}
        description = canonical
        if variant == "near_duplicate":
            description = canonical.replace("STEEL", "CARBON STEEL").replace("BOLT", "HEX BOLT")
        elif variant == "abbreviation":
            for source, target in _ABBREVIATIONS.items():
                description = description.replace(source, target)
        elif variant == "multilingual":
            description = _TRANSLATIONS.get(family_id, f"MATÉRIEL {canonical}")
        elif variant == "unit_format":
            description = description.replace("50 MM", "50mm").replace("M10", "10 mm").replace("240 V", "240VAC")
        elif variant == "terminology":
            description = description.replace("BOLT", "FASTENER").replace("PIPE", "TUBE")
        if variant == "near_duplicate" and family_id in ("bolt_b", "bolt_c"):
            # Keep B and C as separate labelled groups despite lexical similarity.
            pass
        records.append({
            "record_id": f"cpse-{index + 1:05d}",
            "source": ("erp", "catalogue", "maintenance")[index % 3],
            "material_code": f"{family_id.upper()}-{index + 1:05d}",
            "description": description,
            "attributes": dict(attrs),
            "ground_truth_group": family_id,
            "variant": variant,
        })
    rng.shuffle(records)
    return records


# Descriptive alias for callers that want to make the synthetic nature clear.
generate_synthetic_dataset = generate_dataset
