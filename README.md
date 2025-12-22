# rag-demo (FastAPI + Postgres/pgvector + OpenAI)

A deliberately small, interview-friendly **RAG** demo you can run:

- **Locally** with `uvicorn`
- **Locally in Docker** (optimized for **linux/arm64** dev)
- **On AWS** using **ECR + ECS Fargate** (runs **linux/amd64**), provisioned with **Terraform**
- Uses **Postgres + pgvector** for both metadata + vector search (local Postgres in Docker; cloud Postgres via RDS)

This project targets Python 3.13.x.
If you use pyenv: 
```pyenv install 3.13.1 && pyenv local 3.13.1```

## What you get

### API endpoints
- `GET /health` → `{"status":"ok"}`
- `POST /ingest` → chunk + embed + store
- `POST /ask` → embed question + retrieve top-k + call LLM + return answer + citations
- `POST /ingest_dir` → ingest all `.txt` files in `./data/`

### Storage model (Postgres)
- `documents` table (source + metadata)
- `chunks` table (chunk text + embedding vector + position)

### OpenAI integration
- Embeddings via `client.embeddings.create(...)`
- Text generation via `client.responses.create(...)`

If no `OPENAI_API_KEY` is provided, the app runs in **mock mode**:
- embeddings are deterministic (hash-based)
- the “LLM answer” is a simple template
This is useful for CI and for trying the flow without API costs.

---

## Quick start (local)

### 1) Start Postgres (with pgvector)
```bash
docker compose up -d postgres
```

### 2) Create a venv and run FastAPI
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg://rag:rag@localhost:5432/rag"
export OPENAI_MODEL="gpt-5"                # optional
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"  # optional
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

## Run in Docker (local, linux/arm64)

```bash
docker compose up --build
```

API: http://127.0.0.1:8011

---

## AWS deploy (ECR + ECS/Fargate + RDS) with Terraform

### Prereqs
- AWS CLI authenticated
- Terraform installed
- An existing Route53 hosted zone is optional (we output the ALB URL either way)

### 1) Provision infra
```bash
cd infra/terraform/aws
terraform init
terraform apply
```

Terraform outputs:
- `ecr_repository_url`
- `alb_dns_name`
- `rds_endpoint`
- other useful values

### 2) Build and push the image to ECR (linux/amd64)
From repo root:
```bash
./scripts/ecr_build_push.sh <ecr_repository_url> <tag>
```

### 3) Update the ECS service to the new tag
```bash
cd infra/terraform/aws
terraform apply -var="image_tag=<tag>"
```

---

## Configuration

Environment variables:
- `DATABASE_URL` (required)
- `OPENAI_API_KEY` (optional; enables real OpenAI calls)
- `OPENAI_MODEL` (default: `gpt-5`)
- `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- `CHUNK_SIZE` (default: 800 chars)
- `CHUNK_OVERLAP` (default: 120 chars)

---

## Notes
- This is intentionally **not** LangChain — the goal is to be transparent and minimal.
- The AWS setup uses **Fargate**, **ALB**, **CloudWatch Logs**, **Secrets Manager** (for DB password), and **RDS Postgres**.
- pgvector is enabled via `CREATE EXTENSION IF NOT EXISTS vector;` on startup.
- Retrieval uses L2 distance (not cosine) because pgvector 0.8.1 can return no rows for `cosine_distance` when bound parameters are used. If you upgrade pgvector (≥0.9) and configure `ivfflat.probes`, you can switch back to cosine by changing `retrieve_top_k` in `app/rag/retrieval.py`.
- OpenAI calls use the Chat Completions API (`client.chat.completions.create`) for broad client compatibility. If you want to switch to the newer Responses API, ensure your `openai` SDK supports it and update `app/rag/llm.py`.

See:
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
