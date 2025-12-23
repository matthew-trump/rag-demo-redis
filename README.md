# rag-demo-weaviate (FastAPI + Weaviate + OpenAI)

A deliberately small, interview-friendly **RAG** demo you can run locally with `uvicorn`. It stores chunks + embeddings in **Weaviate** and uses **OpenAI** for embeddings/answers (mock mode if no key).

This project targets Python 3.13.x.
If you use pyenv: 
```pyenv install 3.13.1 && pyenv local 3.13.1```

## What you get

### API endpoints
- `GET /health` → `{"status":"ok"}`
- `POST /ingest` → chunk + embed + store
- `POST /ask` → embed question + retrieve top-k + call LLM + return answer + citations
- `POST /ingest_dir` → ingest all `.txt` files in `./data/`

### Storage model (Weaviate)
- One Weaviate collection/class (metric: cosine) with vectors that contain `content`, `source`, `chunk_index` (and your metadata) as properties. Weaviate is a purpose-built vector DB (HNSW ANN, metadata filters, hybrid search, managed or self-hosted) accessed via upsert/query APIs.

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
export WEAVIATE_HOST="localhost"            # local Weaviate default
export WEAVIATE_PORT="8091"
export WEAVIATE_SECURE="false"
# export WEAVIATE_GRPC_PORT="8092"          # optional; set if your Weaviate exposes gRPC
# export WEAVIATE_GRPC_SECURE="false"
export WEAVIATE_API_KEY="..."               # optional for local; required for cloud
export WEAVIATE_CLASS="Chunk"
# export OPENAI_API_KEY="..."              # optional (enables real OpenAI calls)

uvicorn app.main:app --reload --port 8011
```

### 3) Ingest sample docs
```bash
curl -s -X POST http://127.0.0.1:8011/ingest_dir | jq .
```

### 4) Ask a question
```bash
curl -s -X POST http://127.0.0.1:8011/ask   -H "Content-Type: application/json"   -d '{"question":"What is this demo doing?","top_k":4}' | jq .
```

---

## Configuration

Environment variables:
- `OPENAI_API_KEY` (optional; enables real OpenAI calls)
- `OPENAI_MODEL` (default: `gpt-5`)
- `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- `CHUNK_SIZE` (default: 800 chars)
- `CHUNK_OVERLAP` (default: 120 chars)
- `WEAVIATE_HOST` (default: `localhost`)
- `WEAVIATE_PORT` (default: `8091`)
- `WEAVIATE_SECURE` (default: `false`)
- `WEAVIATE_GRPC_PORT` (optional; set if using gRPC)
- `WEAVIATE_GRPC_SECURE` (default: `false`)
- `WEAVIATE_API_KEY` (optional for local; required for cloud)
- `WEAVIATE_CLASS` (default: `Chunk`)

---

## Notes
- This is intentionally **not** LangChain — the goal is to be transparent and minimal.
- Weaviate class creation is automatic if it does not exist (cosine metric, 1536-dim vectors, no built-in vectorizer).
- OpenAI calls use the Chat Completions API (`client.chat.completions.create`) for broad client compatibility. If you want to switch to the newer Responses API, ensure your `openai` SDK supports it and update `app/rag/llm.py`.
- Legacy infra (Terraform under `infra/terraform/aws/`) was written for Postgres; adapt it if you deploy this Weaviate variant.

### Weaviate troubleshooting (what we hit here)
- The v4 Python client prefers gRPC; gRPC kept failing on 8092 (connection reset). We switched to HTTP/REST for schema, inserts, and queries in `app/rag/vector_store.py`.
- Ensure Weaviate is running and reachable on the HTTP port you set (default 8091 here). If you run it locally: `docker run -p 8091:8080 semitechnologies/weaviate:latest ...`.
- If you want gRPC later, map the gRPC port (e.g., `-p 8092:8081`) and align secure/insecure settings; otherwise leave `WEAVIATE_GRPC_PORT` unset and stay HTTP-only.

See:
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
