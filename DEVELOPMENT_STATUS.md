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

## Milestone 2 — AI harmonization engine

**Status: Complete**

- [x] Process multilingual descriptions without an LLM or translation service.
- [x] Generate deterministic local embeddings and support a lazy multilingual
  Sentence Transformer adapter.
- [x] Provide in-memory Top-K cosine retrieval and optional PostgreSQL/pgvector
  persistence with HNSW index SQL.
- [x] Combine semantic, technical-attribute, and terminology scores.
- [x] Apply hard constraints for grade, size, standard, pressure, and voltage.
- [x] Produce configurable EQUIVALENT, REVIEW, or DIFFERENT decisions with
  confidence and explanations.
- [x] Preserve original descriptions and extracted attributes.

## Milestone 3 — Product registry and human review

- [x] Deterministic equivalence clustering using existing matching decisions.
- [x] Canonical material records and unique CNMC-style identifiers.
- [x] Source material-code mappings with append-only mapping history.
- [x] Review workflow for REVIEW candidates with approve/reject/override.
- [x] AI confidence, component scores, explanations, and human decisions.
- [x] Precision, recall, F1, false-positive, and false-negative evaluation.
- [x] Optional lazy Streamlit upload/search/review/statistics dashboard.
- [x] In-memory repositories only; no infrastructure required.

## Future phases — Planned, not implemented

- [ ] Persistent source ingestion and provenance.
- [ ] Authentication, persistence, migrations, deployment, and CI/CD.

Future items require explicit design and acceptance before implementation.
