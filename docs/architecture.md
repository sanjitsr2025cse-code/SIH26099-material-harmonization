# Architecture

## Problem and goal

Material descriptions arrive from different systems with inconsistent naming,
units, abbreviations, and levels of detail. The project goal is to provide a
reliable path from source descriptions to harmonized, reviewable material
records without hiding uncertainty or losing source context.

## Milestone 1 architecture

The current architecture is intentionally a single Python package:

```text
app/
├── main.py                 FastAPI application assembly
├── core/
│   ├── config.py           environment-backed runtime settings
│   └── logging.py          standard-library logging setup
├── api/routes/
│   └── health.py           GET /health
└── pipeline/
    ├── ingestion.py        CSV and Excel loading
    ├── validation.py       schema and record checks
    ├── profiling.py        dataset quality profile
    ├── normalization.py    configurable text normalization
    ├── extraction.py       technical attributes and unit checks
    └── classification.py   transparent keyword categories
```

`app.main:app` loads four settings (`APP_NAME`, `ENVIRONMENT`, `DEBUG`, and
`LOGGING_LEVEL`), configures logging, and registers the health route. The
independent `app.pipeline` package provides in-memory Pandas ingestion,
validation, profiling, normalization, extraction, and rule classification.
There is no persistence, network integration, model loading, or authentication.

## Pipeline flow

The intended future flow is:

1. Ingest CSV/Excel records while retaining `original_description`.
2. Validate required fields, types, missing values, and duplicates.
3. Profile columns and normalize text, units, abbreviations, and synonyms.
4. Extract technical attributes with regex, dictionaries, and rules.
5. Validate extracted values/units and classify using configured keywords.

Later phases may generate representations suitable for semantic comparison,
retrieve candidates, cluster or merge records, and publish a governed registry.

Possible innovations include explainable matches, confidence-aware human review,
incremental learning from corrections, and cross-source provenance. These are
planned ideas, not current capabilities.

## Technology direction (planned)

FastAPI and Python remain the service direction. A future persistence/search
design may evaluate PostgreSQL with pgvector and HNSW indexes, but no database
choice or schema is committed by this phase. Deployment, authentication,
observability, migrations, Docker, Kubernetes, and CI/CD will be designed only
when the corresponding requirements are accepted.
