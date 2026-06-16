# Architecture: Vector Databases & RAG Infrastructure

How the vector databases & rag infrastructure landscape is shaped, and how the Quest tests it.

## The landscape at a glance

| Tool | Tier | License | Focus | Notes |
|------|------|---------|-------|-------|
| Pinecone | A | Proprietary | Managed Vector DB | Market leader (~28% share); zero-ops serverless; $0.033/hr;  |
| Qdrant | A | Apache-2.0 | Vector DB | ~22K stars; Rust-based; self-host + cloud; ACORN filtered HN |
| Weaviate | A | BSD-3-Clause | Vector DB | ~12K stars; hybrid search (BM25+vector); multimodal; GraphQL |
| Milvus | A | Apache-2.0 | Vector DB | ~42K stars; billion-scale; GPU accel; K8s-native; Zilliz Clo |
| Chroma | A | Apache-2.0 | Embedded Vector DB | ~16K stars; developer experience; pip install; Rust rewrite  |
| pgvector | A | PostgreSQL | Postgres Extension | ~13-20K stars; HNSW + IVFFlat; pgvectorscale adds StreamingD |
| Zilliz / Vector Lakebase | A | Proprietary | Managed (Milvus-based) | 100B+ scale; lake-native; S3-based Vortex format; on-demand  |
| Turbopuffer | A | Proprietary | Managed Serverless | Object-storage-first; no namespace limits; 10-100x cheaper a |
| Vorkath | A | Proprietary | Managed Vector DB | Bare-metal NVMe; $1/mo for 1M vec/1M q; no cold starts; Vama |
| LanceDB | A | Apache-2.0 | Embedded/Serverless | ~5K stars; edge, local-first; zero-copy columnar; no server  |
| Elasticsearch / ESRE | A | Elastic/AGPLv3 | Search+Vector | ~30K+ stars; enterprise search; GPU accel in v3.0; re-added  |
| OpenSearch | A | Apache-2.0 | Search+Vector | ~9.5K stars; AWS alternative; GPU-accelerated indexing v3.0; |
| Redis Vector | A | BSD/Proprietary | In-Memory Extension | Sub-ms latency; caching; memory-bound; Redis Enterprise Clou |
| FAISS | A | MIT | ANN Library | ~39K stars; GPU-accelerated billion-scale; Meta; IVF, HNSW,  |
| ScaNN | A | Apache-2.0 | ANN Library | ~31.5K stars; Google-scale inner product; SOAR algorithm; dy |
| LangChain / LangGraph | A | MIT | RAG Framework | ~90K+ combined; chain orchestration; 100+ LLM integrations;  |
| LlamaIndex | A | MIT | RAG Framework | ~40K+ stars; document indexing; retrieval optimization; hier |
| Haystack | A | Apache-2.0 | RAG Framework | Modular search pipelines; enterprise search + LLM integratio |
| Ragas | A | Apache-2.0 | RAG Eval | Most-cited; reference-free RAG evaluation; faithfulness, rel |
| TruLens | A | MIT | RAG Eval+Tracing | ~3.2K stars; production tracing + RAG triad; inline eval; fe |
| DeepEval | A | MIT | RAG Eval | Unit-test-style CI evaluation; pytest integration; agentic e |
| Braintrust | A | Proprietary | RAG Eval+Observability | Production standard; production-to-evaluation feedback; Brai |
| LangSmith | A | Proprietary | LLM Observability | LangChain ecosystem; dataset-driven regression eval; experim |
| Firecrawl | A | Proprietary | Document Parsing | API-first web+PDF → Markdown; Rust-based PDF engine; MCP ser |
| LlamaParse | A | Proprietary | Document Parsing | Agentic OCR for RAG; 90+ formats; 10K free credits/mo; premi |
| Unstructured | A | Apache-2.0 | Document Parsing | 25+ format semantic extraction; element-typed output; hi_res |
| Docling (IBM) | A | MIT | Layout Parser | 61K stars; open-source layout parser; MCP server; LangChain/ |
| Cohere Rerank | A | Proprietary | Reranker | Cross-encoder reranking; rerank-v3.5; multilingual; high ava |
| Voyage AI Rerank | A | Proprietary | Reranker | Instruction-following reranker; rerank-2.5; agent/conversati |
| Glean | A | Proprietary | Enterprise AI Search | 100+ connectors; premium workplace search; $50+/user/mo; clo |
| Microsoft Copilot / M365 | A | Proprietary | Enterprise AI Search | M365 ecosystem; embedded AI across Office; $30/user add-on;  |

## How the Quest tests a tool

Same harness for all entries; the judge was frozen before any tool ran:

```
Adapter[frozen CategoryAdapter contract]
  ├── setup()    → install, configure
  ├── load()     → ingest workload
  ├── await_ready() → async barrier
  ├── query()    → run test, get response
  └── teardown() → cleanup, measure
       ↓
Telemetry: latency · tokens · $ · ops notes
       ↓
Grading: deterministic + LLM judge (frozen prompts)
       ↓
Raw results JSON (published)
```

The `await_ready()` barrier is where async designs get their cost measured instead of hidden.

## License

Content is licensed CC BY 4.0 — share and adapt with attribution to **ArdurAI / Vector Databases & RAG Infrastructure Almanac**.
