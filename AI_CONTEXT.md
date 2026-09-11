# AI Context and Rules

## Project intent

Build a trustworthy material harmonization service that preserves source
provenance, makes uncertainty visible, and supports reviewable canonical data.

## Current boundary

This repository is in Phase 0. Keep changes limited to the documented
foundation unless a later phase is explicitly requested. The health endpoint is
the only API surface.

## Rules for AI-assisted changes

- Inspect the repository before editing and preserve relevant existing work.
- Prefer small, typed, testable changes that follow the current package layout.
- Do not invent domain behavior, schemas, credentials, or external services.
- Keep future pipeline, embeddings, matching, clustering, registry, auth,
  database, deployment, and CI/CD work explicitly planned until approved.
- Add or update focused tests for implemented behavior.
- Use environment variables for runtime configuration; never commit `.env` files
  or secrets.
- Run the relevant tests and import checks before reporting completion.
- Update architecture and status documentation when the approved scope changes.
