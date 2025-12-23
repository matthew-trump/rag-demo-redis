# Repository Guidelines

## Project Structure & Module Organization
- `app/main.py` is the FastAPI entrypoint; `app/rag/` holds core modules (`api.py` routes, `vector_store.py` for Weaviate, `chunking.py`, `embeddings.py`, `retrieval.py`, `llm.py`, `prompts.py`, `settings.py`).
- `data/` contains sample `.txt` files for `/ingest_dir`.
- `docker/` has the service `Dockerfile`; `infra/` and `scripts/` remain for containerization and infra scaffolding (adapt as needed).
- Python version is pinned to 3.13.1 (`.python-version`), dependencies in `requirements.txt`.

## Build, Test, and Development Commands
- Create venv + install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run API locally (hot reload): `uvicorn app.main:app --reload --port 8011`
- Weaviate env: set `WEAVIATE_HOST`/`WEAVIATE_PORT`/`WEAVIATE_SECURE` (e.g., `localhost:8091`, secure=false for local), `WEAVIATE_API_KEY` (if needed), `WEAVIATE_CLASS`; set `OPENAI_API_KEY` to leave mock mode.
- Local Docker (optional): `docker build -t rag-demo .`.

## Coding Style & Naming Conventions
- Python 3.13, PEP 8, 4-space indent; favor type hints (as in `settings.py`), snake_case for modules/functions, UPPER_SNAKE for constants/env keys.
- Keep FastAPI routers lean; push logic into `app/rag/*` helpers. Keep Pinecone access isolated in `vector_store.py`.
- Imports ordered stdlib → third-party → local. Keep docstrings/comments minimal and focused on non-obvious behavior.

## Testing Guidelines
- Prefer `pytest`; place tests under `tests/` mirroring `app/rag/` modules. Use mock mode (omit `OPENAI_API_KEY`) for deterministic outputs.
- For endpoint checks, hit a running dev server with `curl` (see README examples) and include relevant request/response payloads.
- Aim to cover chunking, retrieval, and prompt construction; avoid making tests depend on live OpenAI.

## Commit & Pull Request Guidelines
- Recent history uses concise, present-tense messages (e.g., `chore: pin python version 3.13.1`); follow that style and keep scope narrow.
- In PRs, provide: summary of behavior change, commands run (`uvicorn`, `pytest`, `docker compose`, etc.), config/env changes, and screenshots or sample `curl` responses for API-facing changes.
- Link related issues/tasks when applicable and note any follow-up work or known gaps.

## Security & Configuration Tips
- Do not commit secrets; use `.env` locally and environment variables in deploys. Mock mode prevents accidental OpenAI spend.
- Weaviate Cloud requires an API key; set URL/class per environment. Avoid sending sensitive content to third-party services unless policies allow.
