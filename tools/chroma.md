# Chroma

An AI-native embedding database designed for developer experience. The fastest path from zero to a working RAG prototype — and increasingly a production option with the Rust rewrite and managed cloud.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 78/100 | HNSW-based. Good recall for small-medium datasets. No advanced quantization or index type options |
| **Latency** | 70/100 | p50 ~20ms, p99 ~50-100ms at embedded scale (100K-500K vectors). Slower than dedicated vector DBs |
| **Token Economics** | 90/100 | Free (Apache 2.0). Chroma Cloud: $5 credits free, Team $250/mo. Near-zero infra cost for self-hosted |
| **Scale Behavior** | 55/100 | Comfortable to ~1M vectors. Performance degrades above 500K-1M. Not designed for 10M+ vector workloads |
| **Ops Burden** | 92/100 | `pip install chromadb`. No server, no config, no Docker. In-process or client-server. Zero ops for dev |
| **Developer Experience** | 95/100 | Best DX in the category. NumPy-like API. First-class LangChain integration. Auto-embedding generation |
| **Data Sovereignty** | 85/100 | Fully open-source. Self-hosted, embedded, or client-server. Chroma Cloud for managed |
| **Composite** | **81/100** | Best developer experience. Prototype-to-production path exists. Scale ceiling is the primary constraint |

## Architecture & Deployment

Chroma is an embedding database, not a traditional vector database. It is designed around the developer experience of building AI applications with embeddings. The architecture is intentionally simple.

**Deployment options**:
- **In-process (embedded)**: Runs inside your Python/JS process. Zero setup, zero network latency. Default for development.
- **Client-server**: Standalone server for production or shared access. Persistent storage with SQLite/DuckDB backends.
- **Chroma Cloud**: Managed hosting (beta/early access as of 2026). Serverless, distributed architecture. $5 free credits, then usage-based. Team plan $250/mo.

**Key architectural features**:
- **Rust rewrite (2025)**: 4× faster writes and queries vs. the original Python implementation. Core engine is now Rust-based.
- **Pluggable embedding models**: OpenAI, Cohere, Sentence Transformers, Hugging Face built-in. Auto-vectorize documents at insert time.
- **Document storage alongside vectors**: No separate database needed. Chroma stores both the document and its embedding.
- **Collection-based organization**: Collections = tables. Each collection can have its own embedding model.
- **Metadata filtering**: Basic key-value filtering on queries. No complex nested AND/OR/NOT like Qdrant.

## Key Features

- **Built-in embedding generation**: `collection.add(documents=[...])` automatically embeds using the collection's configured model. No separate embedding pipeline needed.
- **LangChain/LlamaIndex native**: First-class integrations. Chroma is the default vector store in many LLM tutorials and sample projects.
- **Persistent storage**: Automatically saves collections to disk between sessions. SQLite and DuckDB backends.
- **Full-text + regex search**: Added in recent versions. Basic keyword search alongside vector similarity.
- **Collection forking**: Branch and experiment without affecting production data (Chroma Cloud).
- **Web Sync**: Browser-to-cloud synchronization (Chroma Cloud, Nov 2025).
- **BM25 + SPLADE sparse vectors**: Sparse vector search support added for hybrid retrieval.
- **JavaScript/TypeScript client**: Feature parity with Python client as of 2026. Good for Node.js backends.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | Chroma Claim | Independent Result | Verdict |
|--------|-------------|-------------------|---------|
| Rust rewrite speedup | 4× faster | Not independently verified | ⚠️ Pending |
| p50 latency (Cloud, 100K) | ~20ms | ~20-60ms | ✅ Close |
| p99 latency (embedded, 500K+) | — | ~50-100ms | — |
| Scale ceiling | 10M vectors | Degrades above 1M in practice | ⚠️ Conservative |

### Cost at Scale (2026)

| Scale | Self-Hosted | Chroma Cloud | Notes |
|-------|------------|-------------|-------|
| Prototype | $0 | $0 (5 credits) | Free tier sufficient for development |
| 100K vectors | $0 | $0-5 | Near-zero cost |
| 1M vectors | $0 (infra) | $50-150 | Usage-based |
| 10M vectors | $50-200 (infra) | Not recommended | Consider migration to Qdrant/Weaviate |

## Ops Burden

**In-process**: Zero. `pip install chromadb` and you're done. No server, no Docker, no config files.
**Client-server**: Minimal. `chroma run --path /data` starts a server. Good for small team sharing.
**Chroma Cloud**: Zero. Managed by Chroma team.

**Upgrade path**: Smooth within minor versions. The v0.4 architectural rewrite separated client/server cleanly.
**Debugging**: Good error messages. Python stack traces are familiar. Community is active on Discord.
**Backup/restore**: File-based (SQLite/DuckDB). Standard file backup tools work. No special procedures.

## Developer Experience

- **SDKs**: Python (most mature), JavaScript/TypeScript. Both have feature parity as of 2026.
- **API**: REST. Simple and predictable.
- **Frameworks**: Default vector store in LangChain tutorials. LlamaIndex integration. Haystack support.
- **Embedding**: The standout feature. `collection.add(documents=[...])` auto-embeds. This removes one entire pipeline from the RAG stack.
- **Documentation**: Excellent. The "getting started" guide is genuinely 5 minutes to first query.
- **Community**: ~16K GitHub stars. Active Discord. Growing fast but smaller than Qdrant/Milvus.

## Known Issues & Sharp Edges

1. **Scale ceiling**: The primary limitation. Chroma is not designed for 10M+ vectors. Performance degrades noticeably above 1M vectors. Teams outgrow it and migrate to Qdrant, Pinecone, or Weaviate.
2. **No distributed mode**: No horizontal scaling, no sharding, no replication. Single-node only.
3. **No advanced index types**: HNSW only. No IVF, no graph-based alternatives, no quantization options. No GPU acceleration.
4. **No native hybrid search**: Added sparse vectors + full-text in 2025-2026 but less mature than Weaviate's first-class BM25+vector integration.
5. **No native multi-tenancy**: Tenant isolation must be implemented via collection naming or in application layer.
6. **Chroma Cloud maturity**: The managed offering is newer than Pinecone or Qdrant Cloud. Less proven at scale.
7. **Memory-bound**: In-process mode loads everything into memory. Large datasets require client-server mode with persistent storage.

## When to Use / When to Avoid

**Use Chroma when**:
- You're prototyping a RAG app and want it running in 5 minutes
- You're building demos, running in development, or shipping small production apps (<100K vectors)
- You want an embedded database with zero external dependencies
- Your app is a Python script or small web service
- You want built-in embedding generation without managing a separate pipeline
- You're learning vector databases or teaching others

**Avoid Chroma when**:
- You need more than 1 million vectors in production
- You need high availability, automatic replication, or guaranteed SLAs
- You're building a multi-tenant SaaS with strict tenant isolation
- You need thousands of concurrent queries per second
- You need advanced quantization, GPU acceleration, or multiple index types
- You need the most mature hybrid search (Weaviate wins)
- You need complex metadata filtering (Qdrant wins)

## Smoke Gate Result

✅ **Passed** (2026-06-16). Collection creation, 1,000-vector insert with metadata, and recall@10 > 0.8 all passed. Setup time: ~1 minute with `pip install chromadb`. Auto-embedding generation worked without configuration.

## License

Apache-2.0

## Roster Status

**Tier A** — Best developer experience in the category. Retained in Tier A due to unmatched DX and the fastest path from zero to working RAG. Watch: Rust rewrite real-world performance at scale, Chroma Cloud maturity, scale ceiling migration patterns.
