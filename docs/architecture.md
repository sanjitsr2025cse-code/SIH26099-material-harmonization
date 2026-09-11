# Architecture

## Problem and goal

Material descriptions arrive from different systems with inconsistent naming,
units, abbreviations, and levels of detail. The project goal is to provide a
reliable path from source descriptions to harmonized, reviewable material
records without hiding uncertainty or losing source context.

## Phase 0 architecture

The current architecture is intentionally a single Python package:

```text
app/
├── main.py                 FastAPI application assembly
├── core/
│   ├── config.py           environment-backed runtime settings
│   └── logging.py          standard-library logging setup
└── api/routes/
    └── health.py           GET /health
```

`app.main:app` loads four settings (`APP_NAME`, `ENVIRONMENT`, `DEBUG`, and
`LOGGING_LEVEL`), configures logging, and registers the health route. There is
no persistence, network integration, model loading, authentication, or
business-domain abstraction in Phase 0.

## Planned pipeline (not implemented)

The intended future flow is:

1. Ingest source records while retaining provenance.
2. Validate and normalize text, units, and structured attributes.
3. Generate representations suitable for semantic comparison.
4. Retrieve and score candidate canonical materials.
5. Cluster or merge candidates with explicit confidence and review paths.
6. Publish governed registry records and feedback for later improvement.

Possible innovations include explainable matches, confidence-aware human review,
incremental learning from corrections, and cross-source provenance. These are
planned ideas, not current capabilities.

## Technology direction (planned)

FastAPI and Python remain the service direction. A future persistence/search
design may evaluate PostgreSQL with pgvector and HNSW indexes, but no database
choice or schema is committed by this phase. Deployment, authentication,
observability, migrations, Docker, Kubernetes, and CI/CD will be designed only
when the corresponding requirements are accepted.
