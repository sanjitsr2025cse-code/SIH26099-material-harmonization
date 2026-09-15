import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from app.pipeline.attributes import prepare_records
from app.product.registry import MaterialRegistry
from app.harmonization.matching import MaterialMatcher


if len(sys.argv) < 2:
    raise SystemExit('usage: python scripts/compare_registry_metrics.py data/materials_2k.csv')

source = Path(sys.argv[1])
frame = pd.read_csv(source)
records = prepare_records(frame.to_dict('records'))
registry = MaterialRegistry()
registry.ingest(records)

cnmc_count = len(registry.canonicals)
multi_member_groups = sum(1 for canonical in registry.canonicals.values() if len(canonical.member_ids) > 1)
review_pairs = len(registry.review.items)

matcher = MaterialMatcher()
grade_b = next((record for record in records if record.get('ground_truth_group') == 'bolt_b'), None)
grade_c = next((record for record in records if record.get('ground_truth_group') == 'bolt_c'), None)
near_miss_protected = bool(grade_b and grade_c and matcher.compare(grade_b, grade_c).decision != 'EQUIVALENT')

print(f'CNMC_COUNT={cnmc_count}')
print(f'MULTI_MEMBER_GROUPS={multi_member_groups}')
print(f'REVIEW_PAIRS={review_pairs}')
print(f'NEAR_MISS_PROTECTED={near_miss_protected}')
