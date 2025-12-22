# RAG Improvements (Beyond the Minimal Demo)

This repo is deliberately small. A production-grade RAG system often adds:

- **Smarter chunking & preprocessing**: token-aware splits, semantic boundaries, HTML/Markdown parsing, table/code handling, language detection, normalization, deduplication, redaction/PII stripping.
- **Better retrieval**: hybrid dense+BM25, reranking, filters (metadata/permissions), multi-hop queries, query rewriting/expansion, tuned vector indexes (HNSW/IVFFLAT with probes/lists).
- **Prompt optimization**: retrieval compression/summarization, adaptive context length, guardrails/refusal patterns, domain-specific instructions.
- **Feedback loops**: log queries/responses, human feedback, automated evals (precision/recall, groundedness), prompt/retriever tuning over time.
- **Auth & multi-tenancy**: per-user/org access controls, data isolation, permission-aware retrieval.
- **Freshness & updates**: incremental ingest, change detection, retries/dead-letter queues, re-embedding schedules.
- **Scale & reliability**: async pipelines, background workers, caching, rate limiting, backoff/circuit breakers, observability (metrics/tracing), robust error handling/fallbacks.
- **Security & compliance**: secret management, data residency, encryption, audit logging, content filtering.
- **UX/agent flows**: citation highlighting, answer streaming, user-editable context, multi-step/agentic plans, tool use beyond retrieval.
