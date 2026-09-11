# SIH26099 Material Harmonization

SIH26099 Material Harmonization is planned as a system to help normalize and
match material descriptions from heterogeneous sources. The current repository
contains only the deliberately small Phase 0 foundation: a FastAPI process,
environment-backed settings, logging setup, and a health check.

## Current status

Phase 0 is complete. The application starts without a database or external
services, and `GET /health` returns:

```json
{"status": "healthy"}
```

The planned pipeline, machine learning, matching, clustering, registry,
authentication, and production infrastructure are not implemented.

## Local development

1. Create and activate a virtual environment.
2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Optionally copy `.env.example` to `.env` and adjust settings.
4. Run the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

5. Run tests:

   ```powershell
   pytest
   ```

The local health check is available at <http://127.0.0.1:8000/health>.

## Planned direction

Later phases may introduce ingestion and canonicalization, embeddings,
similarity search, matching and clustering, a governed material registry, and
secure APIs. PostgreSQL, pgvector/HNSW, model providers, authentication,
containerization, orchestration, migrations, and CI/CD are future decisions;
none are part of this foundation.

See [docs/architecture.md](docs/architecture.md), [AI_CONTEXT.md](AI_CONTEXT.md),
and [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for the project boundaries
and working rules.
