# Architecture

## Components (minimal RAG)

1. **FastAPI service** (single container)
   - Ingest: chunk → embed → store (Redis + RediSearch)
   - Ask: embed question → retrieve top-k from Redis → generate answer → return citations

2. **Redis (Redis Stack / RediSearch)**
   - Stores chunks + embeddings as hashes with vector fields plus properties (`content`, `source`, `chunk_index`, metadata).
   - Retrieval is a vector similarity query (cosine) via RediSearch.

## Data flow

### Ingest
1. `POST /ingest` (text + optional metadata)
2. Chunking (fixed-size + overlap)
3. Embeddings
4. Upsert N vectors to Redis with properties/metadata

### Ask
1. `POST /ask` (question)
2. Embed question
3. Retrieve top-k similar chunks from Redis
4. Build prompt with:
   - instructions
   - retrieved context (with citations)
   - question
5. Call the LLM
6. Return answer + citations (chunk ids + sources)

## Storage (Redis)
- Hash per chunk with fields: `id`, `content`, `source`, `filename`, `chunk_index`, `embedding` (FLOAT32 bytes, dim 1536).
- RediSearch index (HNSW, cosine) over `embedding`; text/numeric fields for filtering and returning citations.

## Deployments

### Local dev
- API via `uvicorn`
- Redis Stack locally (e.g., `docker run -p 6379:6379 -p 8001:8001 redis/redis-stack:latest`) or a managed Redis with RediSearch enabled.

### Cloud
- Containerize the FastAPI service (e.g., ECS/Fargate or your platform of choice).
- Use a managed Redis Stack/RediSearch offering or your own Redis deployment; configure `REDIS_URL`/`REDIS_INDEX`/`REDIS_PASSWORD` via env vars.
