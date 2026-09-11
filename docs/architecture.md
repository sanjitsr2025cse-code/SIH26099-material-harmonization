# Architecture

## Problem and goal

Material descriptions arrive from different systems with inconsistent naming,
units, abbreviations, and levels of detail. The project goal is to provide a
reliable path from source descriptions to harmonized, reviewable material
records without hiding uncertainty or losing source context.

## Current architecture

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
There is no required persistence, network integration, model loading, or
authentication for local tests. Milestone 2 provides optional adapters for
model loading and PostgreSQL/pgvector persistence.

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
## Milestone 2 harmonization

The additive `app/harmonization` package sits beside the Milestone 1
`app/pipeline` modules. `MultilingualProcessor` uses Unicode normalization,
language hints, and script detection without translation or LLM calls.
`HashingEmbedder` is deterministic and dependency-free; `SentenceTransformerEmbedder`
loads the optional multilingual model lazily and uses hashing when the package
or model is unavailable. `EmbeddingRecord` preserves source text and metadata.

`InMemoryCosineIndex` is the test adapter. `PgVectorCandidateRetriever` emits
top-k pgvector queries, and `persistence.MaterialRepository` provides
SQLAlchemy/psycopg storage configured from `DATABASE_URL`. `create_schema()`
enables `vector`, creates a fixed-dimension vector column, and creates the
cosine HNSW index. No database connection is made at import time.

`MaterialMatcher` combines cosine similarity, extracted technical attributes,
and token terminology. Grade, size, standard, pressure, and voltage conflicts
are hard constraints and immediately produce `DIFFERENT`; otherwise configurable
thresholds produce `EQUIVALENT`, `REVIEW`, or `DIFFERENT` with reasons and
component scores. Original descriptions and extracted attributes are never
discarded.

Optional model, database, threshold, and retrieval defaults are read from
environment variables through `HarmonizationSettings`; callers can still
override them explicitly for tests or tenant-specific behavior.

Production uses `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions).
Tests and explicitly offline development can use the deterministic hashing
embedder instead. A real cloud PostgreSQL URL and a provider with pgvector
enabled are required to verify the database path; no local PostgreSQL server
is assumed.

## Milestone 3 product registry

`app.product.MaterialRegistry` harmonizes incoming records, compares every
pair using `MaterialMatcher`, and uses deterministic union-find to cluster only
`EQUIVALENT` pairs. Stable member ordering selects the canonical record, and
each cluster receives a unique `CNMC-000001` style identifier. Source-system
and material-code mappings are in memory; every new mapping appends a
`MappingEvent` to history.

`ReviewWorkflow` stores `REVIEW` candidates, AI confidence/component scores,
explanations, and human approve/reject/override decisions. `evaluate_decisions`
reports precision, recall, F1, false positives, and false negatives from
labelled pairs. `app.product.dashboard` imports Streamlit only when launched,
so health/API imports and tests remain dependency-free.
