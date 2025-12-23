# rag-demo-pinecone (FastAPI + Pinecone + OpenAI)

A deliberately small, interview-friendly **RAG** demo you can run locally with `uvicorn`. It stores chunks + embeddings in **Pinecone** and uses **OpenAI** for embeddings/answers (mock mode if no key).

This project targets Python 3.13.x.
If you use pyenv: 
```pyenv install 3.13.1 && pyenv local 3.13.1```

## What you get

### API endpoints
- `GET /health` → `{"status":"ok"}`
- `POST /ingest` → chunk + embed + store
- `POST /ask` → embed question + retrieve top-k + call LLM + return answer + citations
- `POST /ingest_dir` → ingest all `.txt` files in `./data/`

### Storage model (Pinecone)
- One Pinecone index (metric: cosine) with vectors that contain `content`, `source`, `chunk_index` (and your metadata) as metadata. Pinecone is a managed, purpose-built vector DB (ANN indexes, metadata filters, replication/scaling) accessible via upsert/query APIs.

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
export PINECONE_API_KEY="..."             # required for real vector storage
export PINECONE_INDEX="rag-demo"          # auto-created if missing
export PINECONE_NAMESPACE="default"
export PINECONE_CLOUD="aws"               # used when creating a serverless index
export PINECONE_REGION="us-east-1"
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
- `PINECONE_API_KEY` (required for real storage; otherwise ingest/query returns 503)
- `PINECONE_INDEX` (default: `rag-demo`, auto-created)
- `PINECONE_NAMESPACE` (default: `default`)
- `PINECONE_CLOUD` (default: `aws`, used if index is created)
- `PINECONE_REGION` (default: `us-east-1`, used if index is created)

---

## Notes
- This is intentionally **not** LangChain — the goal is to be transparent and minimal.
- Pinecone index creation is automatic if it does not exist (serverless spec with `PINECONE_CLOUD`/`PINECONE_REGION`).
- OpenAI calls use the Chat Completions API (`client.chat.completions.create`) for broad client compatibility. If you want to switch to the newer Responses API, ensure your `openai` SDK supports it and update `app/rag/llm.py`.
- Legacy infra (Terraform under `infra/terraform/aws/`) was written for Postgres; adapt it if you deploy this Pinecone variant.

See:
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
