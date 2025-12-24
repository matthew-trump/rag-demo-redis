# rag-demo-redis (FastAPI + Redis/RediSearch + OpenAI)

A deliberately small, interview-friendly **RAG** demo you can run locally with `uvicorn`. It stores chunks + embeddings in **Redis (RediSearch)** and uses **OpenAI** for embeddings/answers (mock mode if no key).

This project targets Python 3.13.x.
If you use pyenv:
```bash
pyenv install 3.13.1 && pyenv local 3.13.1
```

## What you get

### API endpoints
- `GET /health` → `{"status":"ok"}`
- `POST /ingest` → chunk + embed + store
- `POST /ask` → embed question + retrieve top-k + call LLM + return answer + citations
- `POST /ingest_dir` → ingest all `.txt` files in `./data/`

### Storage model (Redis/RediSearch)
- One RediSearch index (HNSW, cosine) over hashes keyed by chunk id, storing `content`, `source`, `filename`, `chunk_index`, and `embedding` (float32 bytes).

### OpenAI integration
- Embeddings via `client.embeddings.create(...)`
- Text generation via `client.chat.completions.create(...)`

If no `OPENAI_API_KEY` is provided, the app runs in **mock mode**:
- embeddings are deterministic (hash-based)
- the “LLM answer” is a simple template
This is useful for CI and for trying the flow without API costs.

---

## Quick start (local)

### 1) Create a venv and run FastAPI
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_MODEL="gpt-5"                # optional
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"  # optional
export REDIS_URL="redis://localhost:6379"  # Redis Stack with RediSearch
export REDIS_INDEX="rag:chunks"
# export REDIS_PASSWORD="..."              # set if your Redis requires auth
# export OPENAI_API_KEY="..."              # optional (enables real OpenAI calls)

uvicorn app.main:app --reload --port 8011
```

### 2) Start Redis Stack locally (with RediSearch)
```bash
docker run -d --name redis-stack \
  -p 6379:6379 -p 8001:8001 \
  redis/redis-stack:latest
```

### 3) Ingest sample docs
```bash
curl -s -X POST http://127.0.0.1:8011/ingest_dir | jq .
```

### 4) Ask a question
```bash
curl -s -X POST http://127.0.0.1:8011/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this demo doing?","top_k":4}' | jq .
```

---

## Configuration

Environment variables:
- `OPENAI_API_KEY` (optional; enables real OpenAI calls)
- `OPENAI_MODEL` (default: `gpt-5`)
- `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- `CHUNK_SIZE` (default: 800 chars)
- `CHUNK_OVERLAP` (default: 120 chars)
- `REDIS_URL` (default: `redis://localhost:6379`)
- `REDIS_PASSWORD` (optional)
- `REDIS_INDEX` (default: `rag:chunks`)

---

## Notes
- This is intentionally **not** LangChain — the goal is to be transparent and minimal.
- Redis/RediSearch index creation is automatic if it does not exist (HNSW, cosine, 1536-dim vectors).
- OpenAI calls use the Chat Completions API (`client.chat.completions.create`) for broad client compatibility. If you want to switch to the newer Responses API, ensure your `openai` SDK supports it and update `app/rag/llm.py`.
- Legacy infra (Terraform under `infra/terraform/aws/`) was written for Postgres; adapt it if you deploy this Redis variant.

See:
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
