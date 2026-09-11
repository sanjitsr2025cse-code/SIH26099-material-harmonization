# Development Status

## Phase 0 — Foundation

**Status: Complete**

- [x] Create minimal FastAPI application package.
- [x] Add environment-backed app name, environment, debug, and logging settings.
- [x] Add configurable standard-library logging setup.
- [x] Add `GET /health` with a stable healthy JSON response.
- [x] Add focused health endpoint test.
- [x] Add local setup documentation and architecture boundaries.
- [x] Keep database, ML, matching, clustering, registry, auth, deployment, and
  CI/CD out of scope.

## Milestone 1 — Data foundation

**Status: Complete**

- [x] Ingest CSV and Excel files with source description preservation.
- [x] Validate required fields, basic types, missing values, duplicates, and
  invalid records with structured results.
- [x] Produce basic column and dataset profiles.
- [x] Configurable case, whitespace, punctuation, units, abbreviations, and
  synonym normalization.
- [x] Regex, dictionary, and rule-based technical attribute extraction with
  attribute/unit validation.
- [x] Configurable transparent material-category classification.
- [x] Add representative component tests while preserving `GET /health`.
- [x] Keep all persistence, ML, matching, and infrastructure concerns out of
  scope.

## Future phases — Planned, not implemented

- [ ] Persistent source ingestion and provenance.
- [ ] Embeddings and similarity retrieval.
- [ ] Matching, clustering, confidence, and human review.
- [ ] Governed material registry and supporting APIs.
- [ ] Authentication, persistence, migrations, deployment, and CI/CD.

Future items require explicit design and acceptance before implementation.
