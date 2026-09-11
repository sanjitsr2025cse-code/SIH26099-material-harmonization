# SIH26099 Material Harmonization

SIH26099 Material Harmonization helps normalize and match material descriptions
from heterogeneous sources. The current repository contains the Phase 0
FastAPI foundation, the Milestone 1 Pandas data foundation, and a pre-LLM
Milestone 2 harmonization engine.

## Current status

Milestone 1 is complete. CSV and Excel records can be ingested, validated,
profiled, normalized, rule-extracted, and assigned transparent keyword
categories. Source descriptions are retained in `original_description`.
The application still starts without a database or external services, and
`GET /health` returns:

```json
{"status": "healthy"}
```

Milestone 2 adds an additive `app/harmonization` package: translation-free
multilingual normalization, optional lazy multilingual embeddings (with a
deterministic hashing fallback), top-k cosine retrieval, explainable hybrid
matching, and an optional PostgreSQL/pgvector persistence adapter. Clustering,
CNMC registry, UI, auth, queues, containers, and external APIs remain out of
scope.

## Local development

Windows PowerShell:

1. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

2. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Optionally copy `.env.example` to `.env` and adjust settings.
5. Run tests:

   ```powershell
   python -m pytest
   ```

6. Run the API:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

The local health check is available at <http://127.0.0.1:8000/health>.

### Pipeline usage

```python
from app.pipeline.ingestion import ingest_file
from app.pipeline.pipeline import MaterialPipeline

records = ingest_file("materials.csv")
result = MaterialPipeline().run(records)
print(result.validation.valid, result.profile.row_count)
```

The pipeline modules under `app/pipeline` are independently testable. They
perform no persistence, network calls, embeddings, or model inference.

### Milestone 2 harmonization

```python
from app.harmonization import HashingEmbedder, MaterialMatcher, MultilingualProcessor

text = MultilingualProcessor().process("Acero inoxidable 10 mm")
vector = HashingEmbedder().embed(text.normalized)
decision = MaterialMatcher().compare(
    {"normalized_description": text.normalized, "embedding": vector, "attributes": {"size": "10 mm"}},
    {"normalized_description": text.normalized, "embedding": vector, "attributes": {"size": "10 mm"}},
)
```

The fallback performs no network access or model download. To enable the
PostgreSQL adapter install the commented `sqlalchemy` and `psycopg[binary]`
packages and set `DATABASE_URL`. `sentence-transformers` is similarly
optional; its model is loaded only on first use and falls back automatically.
Optional defaults can be configured with `EMBEDDING_MODEL`,
`MATCH_EQUIVALENT_THRESHOLD`, `MATCH_REVIEW_THRESHOLD`, and
`RETRIEVAL_TOP_K`.

## Planned direction

Later phases may introduce a governed material registry and secure APIs.
PostgreSQL/pgvector persistence and HNSW retrieval are available as optional
deployment integrations. Authentication, containerization, orchestration,
migrations, and CI/CD remain future decisions.

See [docs/architecture.md](docs/architecture.md), [AI_CONTEXT.md](AI_CONTEXT.md),
and [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for the project boundaries
and working rules.
