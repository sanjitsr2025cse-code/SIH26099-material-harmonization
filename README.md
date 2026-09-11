# SIH26099 Material Harmonization

SIH26099 Material Harmonization is planned as a system to help normalize and
match material descriptions from heterogeneous sources. The current repository
contains the Phase 0 FastAPI foundation and a deliberately pre-ML Milestone 1
Pandas pipeline for inspecting and preparing material descriptions.

## Current status

Milestone 1 is complete. CSV and Excel records can be ingested, validated,
profiled, normalized, rule-extracted, and assigned transparent keyword
categories. Source descriptions are retained in `original_description`.
The application still starts without a database or external services, and
`GET /health` returns:

```json
{"status": "healthy"}
```

ML, matching, clustering, registry, authentication, and production
infrastructure are not implemented.

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

## Planned direction

Later phases may introduce ingestion and canonicalization, embeddings,
similarity search, matching and clustering, a governed material registry, and
secure APIs. PostgreSQL, pgvector/HNSW, model providers, authentication,
containerization, orchestration, migrations, and CI/CD are future decisions;
none are part of this foundation.

See [docs/architecture.md](docs/architecture.md), [AI_CONTEXT.md](AI_CONTEXT.md),
and [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for the project boundaries
and working rules.
