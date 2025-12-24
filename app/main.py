import logging
from fastapi import FastAPI
from app.rag.api import router as rag_router
from app.rag.settings import settings

app = FastAPI(title="rag-demo", version="0.1.0")
logger = logging.getLogger(__name__)

# Ensure our module logs show up when running under uvicorn.
logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
def _startup() -> None:
    logger.info(
        "Starting with mode=%s, milvus_uri=%s, milvus_collection=%s",
        settings.mode,
        settings.milvus_uri,
        settings.milvus_collection,
    )

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": settings.mode}

app.include_router(rag_router)
