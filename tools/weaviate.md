# Weaviate

An open-source vector database with the most mature hybrid search (BM25 + vector) and strong multimodal support. Go-based, with GraphQL-native API.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 89/100 | Hybrid search outperforms pure vector by 12-18% on domain-specific corpora. Named vectors for multimodal. MMR diversity search |
| **Latency** | 82/100 | p50 ~1.8ms, p99 ~5.8ms at small scale; p99 rises to 16-50ms at 10M+ vectors depending on configuration |
| **Token Economics** | 72/100 | Serverless Cloud: $25/mo + $0.095/1M dimensions. Self-hosted: predictable infra cost. BQ reduces 100M vectors from $1,459 to ~$45/mo |
| **Scale Behavior** | 80/100 | Horizontal scaling with sharding. K8s-native. Higher memory consumption than Qdrant for equivalent datasets |
| **Ops Burden** | 68/100 | Docker is easy; K8s production requires Helm expertise. Module system adds config overhead |
| **Developer Experience** | 85/100 | GraphQL API is clean for complex queries. Built-in vectorization modules. Schema-based (can be rigid) |
| **Data Sovereignty** | 88/100 | Open-source (BSD-3), Docker, K8s, BYOC, Enterprise Cloud on AWS with HIPAA. SOC 2 Type II |
| **Composite** | **81/100** | Best hybrid search and multimodal. The choice when keyword + vector is non-negotiable |

## Architecture & Deployment

Weaviate is written in Go. It is designed as a cloud-native vector database with modular AI integrations. The architecture separates data nodes, query nodes, and vectorizer modules.

**Deployment options**:
- **Self-hosted (Docker)**: Single-node for development. Straightforward with Docker Compose.
- **Self-hosted (Kubernetes)**: Production deployment via Helm chart. Includes built-in HPA for query and data nodes separately (improved 2026).
- **Weaviate Cloud Services (WCS) Shared**: Serverless/pay-as-you-go. $25/mo base + $0.095/1M dimensions/month (Standard tier).
- **Weaviate Cloud Services Dedicated**: Isolated resources. Enterprise adds HIPAA, SLAs, premium support.
- **BYOC**: Enterprise Cloud on AWS. Managed software on customer-controlled infrastructure.

**Key architectural features**:
- **Modular vectorizer system**: Built-in modules for OpenAI, Cohere, Hugging Face, Google, Anthropic embeddings. Auto-generate embeddings on insert/query.
- **Hybrid search**: BM25 + HNSW vector search in a single query with configurable `alpha` parameter. Maturest in the category.
- **Named vectors**: Single object can carry multiple independent vector representations (e.g., image + text). Critical for multimodal RAG.
- **Native multi-tenancy**: Isolated data partitions per tenant within a single cluster. Per-tenant backup, deletion, load isolation.
- **GraphQL-first API**: Native GraphQL with `nearText`, `nearVector`, `bm25`, `hybrid` queries.

## Key Features

- **MCP Server** (v1.37, April 2026): Built-in MCP server at `/v1/mcp` enabling Claude, Cursor, VS Code to query and write directly. Most architecturally significant release of April 2026.
- **Incremental Backups** (v1.37): Backup only changed data, reducing backup time and cost.
- **Diversity Search (MMR)**: Maximal Marginal Relevance for result diversity. Reduces redundancy in retrieval.
- **Query Profiling**: Built-in query profiling tools for performance optimization.
- **BlobHash**: Content-addressed blob storage for large objects.
- **Engram memory layer** (beta): Memory layer for agents. Interaction records, topic organization, merge/delete capabilities.
- **Generative modules**: RAG-style answer generation directly from Weaviate queries (Claude 3 Opus/Sonnet, GPT-4o).
- **Binary Quantization**: 32× compression. Reduces 100M vectors from $1,459/month to ~$45/month on Cloud.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | Weaviate Claim | Independent Result | Verdict |
|--------|---------------|-------------------|---------|
| p50 latency | 1.8ms | ~1.8-5ms (small scale) | ✅ Close |
| p99 latency, 10M vectors | 16ms | ~16-50ms (varies by config) | ✅ Close |
| Hybrid recall improvement | +12-18% over pure vector | ~10-15% on domain corpora | ✅ Close |
| QPS | 5.8K | Varies by workload | — |
| Recall@10 | 96-97% | ~96-97% on standard benchmarks | ✅ Close |

### Cost at Scale (2026 pricing)

| Scale | WCS Shared (Standard) | Self-Hosted | Notes |
|-------|------------------------|-------------|-------|
| 1M vectors (768-dim) | ~$73/mo | $25-50/mo (VPS) | Without BQ |
| 10M vectors (768-dim) | ~$730/mo | $96-150/mo | Without BQ |
| 100M vectors (768-dim) | ~$1,459/mo | $200-400/mo | Without BQ |
| 100M vectors (768-dim) + BQ | ~$45/mo | $200-400/mo (infra) | BQ is free on Cloud; infra cost fixed on self-hosted |

**Pricing model**: Dimension-based billing on Cloud. Formula: `vector_count × dimension_size × replication_factor × $0.095/1M dims`. Enable BQ in production.

## Ops Burden

**Docker**: Low. Docker Compose setup in ~10 minutes. Good for development.
**Kubernetes**: Moderate to high. Helm chart is well-maintained but requires K8s expertise. 2026 update added built-in HPA configurations, reducing manual setup.
**Cloud**: Low. WCS handles operations. Pricing can be unpredictable without BQ.

**Upgrade path**: Generally smooth within minor versions. Schema migrations are managed. The module system can cause breaking changes when vectorizer APIs change.
**Debugging**: Good. Query profiling tools help. GraphQL errors are sometimes verbose. Logs are structured.
**Backup/restore**: Incremental backups (v1.37) reduce time and cost. Self-hosted requires configuring S3/GCS backup targets.

## Developer Experience

- **SDKs**: Python (most mature), Go, Java, JavaScript/TypeScript, PHP, Ruby, C# (added Jan 2026), Java v6 client.
- **API**: GraphQL (native) + REST + gRPC. GraphQL is excellent for complex queries but has a learning curve.
- **Schema**: Must define schemas upfront. More rigid than Qdrant's schema-less approach but enables stronger typing and validation.
- **Vectorizers**: Optional built-in embedding generation. Can auto-vectorize on insert. This is genuinely useful for teams without embedding pipelines.
- **Modules**: Pluggable system for vectorizers, rankers, generators, readers. Adds flexibility but also configuration complexity.
- **Frameworks**: LangChain + AI Agents, LlamaIndex, Haystack, Streamlit. MCP server (v1.37) is a major integration win.

## Known Issues & Sharp Edges

1. **Higher memory consumption**: Self-hosting Weaviate requires more RAM than Qdrant for equivalent datasets. Plan for 2-4× memory overhead vs. Qdrant with BQ.
2. **Schema rigidity**: Must define schemas upfront. Less flexible than schema-less databases for rapidly evolving data models.
3. **Cloud pricing confusion**: Dimension-based billing confuses users who expect per-vector pricing. Without BQ, costs scale linearly with dimensions and can surprise.
4. **Learning curve**: Module system, GraphQL, schema definition — all add cognitive load. Newer teams find Qdrant or Pinecone easier.
5. **Self-hosted K8s complexity**: Production deployment requires Kubernetes expertise. Not a single-binary experience like Qdrant.

## When to Use / When to Avoid

**Use Weaviate when**:
- Hybrid search (BM25 + vector) is non-negotiable
- You need multimodal search (text + image + audio + video) in one database
- You're building a B2B SaaS and need native multi-tenancy with tenant isolation
- You need regulated deployment (HIPAA, SOC 2) with self-hosting or BYOC
- You want built-in vectorization modules to skip embedding pipeline management
- You need diversity search (MMR) for result variety

**Avoid Weaviate when**:
- Your team is new to vector databases and wants the fastest learning curve (Qdrant or Pinecone are easier)
- Memory is constrained and you need maximum vectors per GB of RAM (Qdrant with BQ wins)
- You need the absolute lowest p99 latency at billion scale (Milvus or Qdrant may win)
- You want a schema-less experience (Qdrant is more flexible)
- You need GPU-accelerated indexing (Milvus wins)

## Smoke Gate Result

✅ **Passed** (2026-06-16). Schema creation, 1,000-vector insert with metadata, hybrid query (BM25 + vector), and recall@10 > 0.8 all passed. Setup time: ~8 minutes with Docker Compose.

## License

BSD-3-Clause

## Roster Status

**Tier A** — Best hybrid search and multimodal support. Retained in Tier A due to unique differentiation in hybrid retrieval and multimodal RAG. Watch: MCP server adoption, cloud pricing transparency, memory efficiency improvements.
