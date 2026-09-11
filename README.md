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
matching, and an optional PostgreSQL/pgvector persistence adapter. Milestone 3
adds `app.product`: deterministic matching-decision clusters, canonical
CNMC-style records, append-only source-code mappings, human review, and
evaluation metrics, all in memory.

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

The production configuration uses `sentence-transformers` with
`paraphrase-multilingual-MiniLM-L12-v2` and a 384-dimensional pgvector column.
The model is loaded only on first use. The deterministic hashing embedder
remains available for tests and explicitly offline development.

Set `DATABASE_URL` in a local, untracked `.env` file to your cloud PostgreSQL
provider's SQLAlchemy URL, for example:

```text
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE?sslmode=require
```

Then initialize the extension, table, and HNSW index with
`MaterialRepository().create_schema()`. The cloud database must have the
pgvector extension available; this repository does not install or run
PostgreSQL locally.
Optional defaults can be configured with `EMBEDDING_MODEL`,
`MATCH_EQUIVALENT_THRESHOLD`, `MATCH_REVIEW_THRESHOLD`, and
`RETRIEVAL_TOP_K`.

### Milestone 3 registry and review

```python
from app.product import MaterialRegistry

registry = MaterialRegistry()
registry.ingest([
    {"record_id": "a", "source": "erp", "material_code": "10",
     "description": "stainless steel bolt 10 mm"},
    {"record_id": "b", "source": "catalogue", "material_code": "B-10",
     "description": "stainless steel bolt 10 mm"},
])
print(registry.list_canonicals()[0].cnmc_id)
```

Uncertain pairs are available through `registry.candidates()` and can be
approved, rejected, or overridden with `registry.decide_review(...)`. The
optional dashboard is lazy: install the commented `streamlit` dependency and
run `streamlit run app/product/dashboard.py`.

## Planned direction

Later phases may introduce a governed material registry and secure APIs.
PostgreSQL/pgvector persistence and HNSW retrieval are configured for the
external database described above. Authentication, containerization,
orchestration, migrations, and CI/CD remain future decisions.

### 10K validation benchmark

The deterministic offline milestone benchmark generates 10,000 CPSE-style
records, including duplicate and near-duplicate descriptions, multilingual and
abbreviated terminology, unit variations, unrelated products, and hard
attribute near-misses. It uses the existing Pandas pipeline, hashing
embeddings, in-memory cosine retrieval (the offline analogue of pgvector/HNSW),
and accepts an injected embedder or `MaterialRepository` for integration
measurements:

```powershell
python scripts\benchmark_10k.py
python scripts\benchmark_10k.py --postgres
python -m pytest tests\test_benchmark.py
```

The JSON report includes record count, processing/embedding/database/HNSW/
matching/total timings, decision counts, canonical groups, duplicate
reduction, and precision/recall/F1 against generated group labels. The default
command is deterministic and offline. `--postgres` uses the configured
`DATABASE_URL`, `MaterialRepository`, pgvector persistence, and the HNSW
candidate retriever with reproducible 384-dimensional hashing embeddings and
removes its temporary `cpse-*` rows after reporting. In particular,
`STEEL BOLT M10 GRADE B` and `STEEL BOLT M10 GRADE C` are explicitly checked
never to merge because Grade is a hard attribute.

See [docs/architecture.md](docs/architecture.md), [AI_CONTEXT.md](AI_CONTEXT.md),
and [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for the project boundaries
and working rules.
