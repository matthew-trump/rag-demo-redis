# Milvus Troubleshooting (what finally worked)

These are the steps and fixes that got Milvus running reliably for this demo.

## Container setup
- Use the Milvus + MinIO compose pair; do **not** rely on embedded MinIO defaults. Example:
  ```yaml
  services:
    milvus-minio:
      image: quay.io/minio/minio:latest
      command: server /data --console-address ":9001"
      environment:
        MINIO_ROOT_USER: minioadmin
        MINIO_ROOT_PASSWORD: minioadmin
      ports: ["9000:9000", "9001:9001"]
    milvus:
      image: milvusdb/milvus:v2.4.6
      command: milvus run standalone
      environment:
        ETCD_USE_EMBED: "true"
        PULSAR_USE_EMBED: "true"
        MINIO_ADDRESS: "milvus-minio:9000"
        MINIO_ACCESS_KEY: "minioadmin"
        MINIO_SECRET_KEY: "minioadmin"
        MINIO_USE_SSL: "false"
      depends_on: [milvus-minio]
      ports: ["19530:19530", "9091:9091"]
  ```
- Common crash reason: Milvus can’t reach MinIO (`localhost:9000` connection refused). Fix by using the above compose (MinIO service + envs).

## Python client quirks
- `pymilvus` pulls `environs`, which expects `marshmallow.__version_info__` and `missing=` support. We hit import errors with marshmallow 4.x; pinning `marshmallow==3.21.1` solved it. A small shim in `app/rag/vector_store.py` also patches marshmallow/environs defensively.

## Collection schema / index
- When schema changes (e.g., adding `filename`), drop the collection then restart the API to let it recreate:
  ```python
  from pymilvus import MilvusClient
  c = MilvusClient(uri="http://127.0.0.1:19530")
  if c.has_collection("rag_demo"):
      c.drop_collection("rag_demo")
  ```
- Index params must be a list of dicts:
  ```python
  index_params=[{"index_type": "AUTOINDEX", "metric_type": "COSINE", "field_name": "embedding"}]
  ```

## Retrieval returning `source: unknown`
- Even with fields present, search hits sometimes omit `source`/`filename`. Fix: perform a follow-up `query` by hit IDs to fetch full metadata (implemented in `query_top_k`), and fall back to `filename` before “unknown”.
- Ensure `output_fields` for search/query include `source` and `filename`.

## Ports / URIs
- gRPC: `http://127.0.0.1:19530`
- REST: `http://127.0.0.1:9091`
If one fails, try the other for client connectivity.

## Quick verification
```python
from pymilvus import MilvusClient
c = MilvusClient(uri="http://127.0.0.1:19530")
print(c.list_collections())
print(c.describe_collection("rag_demo"))
rows = c.query("rag_demo", filter="", output_fields=["id","source","filename","chunk_index","content"], limit=5)
for r in rows: print(r)
```

If you see MinIO connection errors in logs, or `source` still shows as unknown, re-check the compose envs, drop/recreate the collection, and ensure the API restart picks up the latest `vector_store.py`.
