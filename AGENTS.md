# Repository Guidelines

## Project Structure & Module Organization
- `app/main.py` is the FastAPI entrypoint; `app/rag/` holds `api.py` (routes), `vector_store.py` (Milvus), `chunking.py`, `embeddings.py`, `retrieval.py`, `llm.py`, `prompts.py`, `settings.py`.
- `data/` contains sample `.txt` files for `/ingest_dir`.
- `docker/` holds the container `Dockerfile`; `infra/` and `scripts/` are scaffolding for deployments (adapt as needed).
- Python 3.13.1 is pinned (`.python-version`); dependencies in `requirements.txt`.

## Build, Test, and Development Commands
- Create venv + install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run API locally (hot reload): `uvicorn app.main:app --reload --port 8011`
- Milvus env: set `MILVUS_URI` (e.g., `http://localhost:19530`), `MILVUS_COLLECTION` (e.g., `rag_demo`), optional `MILVUS_TOKEN`; set `OPENAI_API_KEY` to leave mock mode.
- Local Docker (optional): `docker build -t rag-demo .`.

## Coding Style & Naming Conventions
- Python 3.13, PEP 8, 4-space indent; favor type hints and snake_case; constants/env keys in UPPER_SNAKE.
- Keep FastAPI routers thin; put Milvus access in `vector_store.py` and business logic in helpers.
- Imports ordered stdlib → third-party → local. Only comment non-obvious behavior.

## Testing Guidelines
- Use `pytest`; tests live in `tests/` mirroring `app/rag/` modules. Mock mode (no `OPENAI_API_KEY`) yields deterministic embeddings/answers.
- For endpoint checks, hit a running dev server with `curl` (see README) and capture request/response snippets.
- Cover chunking, retrieval, and prompt construction; avoid making tests depend on live OpenAI.

## Commit & Pull Request Guidelines
- History uses short, present-tense messages (e.g., `chore: pin python version 3.13.1`); follow that style and keep scope tight.
- PRs should include a brief summary, commands run (`uvicorn`, `pytest`, etc.), env/config changes, and sample `curl` outputs for API changes. Link issues/tasks where relevant.

## Security & Configuration Tips
- Never commit secrets; use `.env` locally and env vars in deployments. Mock mode protects against accidental OpenAI spend.
- Milvus can be local or managed; set `MILVUS_TOKEN` only when your deployment requires auth. Do not send sensitive content to external services unless policy allows.
