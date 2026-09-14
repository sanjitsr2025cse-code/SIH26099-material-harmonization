# CPSE workflow fixtures

`dataset_A.csv` through `dataset_H.csv` are deterministic, generated fixtures
for upload, accounting, grouping, and matching tests. Regenerate them with:

```powershell
python scripts\generate_test_datasets.py
```

Every file has the same contract:

- `record_id`
- `cpse_organization` and `source_organization`
- `material_code`
- `original_description`
- JSON `attributes`
- `ground_truth_group`
- `variant`

Datasets A–G contain 48 records and intentionally exercise exact, near
duplicate, multilingual, abbreviated, unit-format, terminology, and unrelated
variants respectively. Dataset H contains 10,000 records and is the large
upload/accounting fixture. The files are generated from the existing
`generate_dataset` implementation, so the benchmark generator remains
backward-compatible and matching decisions are unchanged.
