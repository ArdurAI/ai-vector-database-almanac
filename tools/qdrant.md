# Qdrant

A Rust-based open-source vector database with best-in-class metadata filtering and binary quantization. Self-host, cloud, or BYOC.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 90/100 | HNSW + ACORN filtered index; strong recall with metadata filtering. Binary quantization (32× compression) at minimal recall loss |
| **Latency** | 94/100 | p50 ~4ms, p99 ~12-25ms at 10M vectors. Fastest among open-source dedicated vector DBs |
| **Token Economics** | 88/100 | Self-hosted: $20-96/mo fixed for 1-10M vectors. Cloud: $0.014/hr per node. Zero per-query billing on self-hosted |
| **Scale Behavior** | 85/100 | Binary quantization enables 320M logical vectors on a 16GB Droplet. Single-node to distributed cluster with Raft consensus |
| **Ops Burden** | 75/100 | Single binary or Docker for small scale; cluster mode requires 3+ nodes and Raft understanding |
| **Developer Experience** | 82/100 | Good SDKs (Python, Rust, Go, JS/TS). REST + gRPC. Filtering API is best-in-class. Docs improve quarterly |
| **Data Sovereignty** | 92/100 | Full self-hosting, Docker, K8s, BYOC. GDPR Article 44 compliant. SOC 2 Type II on Cloud |
| **Composite** | **86/100** | Best self-hosted dedicated vector DB. The migration target when Pinecone bills exceed $300/mo |

## Architecture & Deployment

Qdrant is written in Rust from the ground up. The Rust implementation produces consistently lower latencies than Go-based or Python-based alternatives. It supports single-node, clustered, and cloud deployments.

**Deployment options**:
- **Self-hosted (single binary)**: Download a binary, point it at storage, run. Handles 1-2M vectors with 8GB RAM. Development-only or hobby-scale without replication.
- **Self-hosted cluster**: 3+ nodes with Raft consensus. Relatively easy compared to Milvus K8s complexity.
- **Qdrant Cloud**: Free 1GB tier; usage-based clusters from $0.014/hr per node. No per-query fees.
- **Qdrant Cloud Enterprise**: GPU-accelerated indexing, Multi-AZ clusters, audit logging (added ~April 2026).
- **BYOC**: Run managed Qdrant in your own cloud infrastructure.

**Key architectural features**:
- **ACORN filtered HNSW**: Optimized for metadata filtering combined with vector search. Pre-filtering reduces search space before HNSW traversal.
- **Binary Quantization**: 32× compression. 10M vectors with BQ use ~1.92GB RAM on a 16GB Droplet, leaving 14GB headroom.
- **Multi-vector / ColBERT support**: Native support for multiple vectors per document (e.g., late interaction models).
- **Payload indexing**: Fast metadata filtering with multiple index types (keyword, integer, float, geo, bool).

## Key Features

- **Native multi-vector / ColBERT**: Supports late interaction retrieval models natively.
- **Relevance Feedback Query** (v1.17): Query-time relevance feedback for iterative search improvement.
- **Binary Quantization (BQ)**: 32× memory reduction with configurable recall trade-off. Widely adopted in 2026 for memory-constrained deployments.
- **Scalar Quantization**: 4× compression. Alternative to BQ when recall loss must be minimized.
- **Hybrid search**: Sparse-dense vectors. Less mature than Weaviate's BM25 integration but improving.
- **Vector Lakebase integration**: Zilliz partnership for lake-native storage (Tier A tool, see `zilliz-vector-lakebase.md`).

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | Qdrant Claim | Independent Result | Verdict |
|--------|-------------|-------------------|---------|
| p50 latency, 10M vectors | 4ms | ~4-8ms | ✅ Close |
| p99 latency, 10M vectors | 12ms | ~12-35ms (varies by load) | ✅ Close |
| Recall@100, SIFT1M | 99%+ | Not independently verified | ⚠️ Pending |
| QPS at 10M vectors | High | 26-35ms p99 under 10-agent concurrent load | ✅ Close |
| BQ compression | 32× | ~30-32× with <2% recall loss | ✅ Close |

### Cost at Scale (March 2026 pricing)

| Scale | Self-Hosted | Qdrant Cloud | Pinecone Equivalent |
|-------|------------|--------------|---------------------|
| 1M vectors | $20-40/mo (VPS) | $9/mo | ~$25-50/mo |
| 10M vectors | $96/mo (16GB DO Droplet) | ~$30-60/mo | ~$78-199/mo |
| 50M vectors (BQ) | $96-192/mo | ~$120-250/mo | ~$800-1,200/mo |
| 100M vectors | $192-384/mo | Custom | ~$1,500-2,500/mo |

**The crossover point**: When Pinecone Serverless exceeds $300/month, self-hosted Qdrant recovers migration engineering cost within 60 days. At 20M vectors / 50K queries daily, self-hosted Qdrant saves ~$2,387/month vs. Pinecone Serverless.

## Ops Burden

**Single-node**: Extremely low. Single binary, Docker one-liner. Setup time: <5 minutes.
**Cluster**: Moderate. Requires understanding Raft consensus, shard placement, and node failure handling. Still simpler than Milvus K8s deployment.
**Cloud**: Zero ops. Qdrant Cloud handles everything.

**Upgrade path**: Generally smooth. Index format is stable. Qdrant publishes migration guides for major versions.
**Debugging**: Good. Rust error messages are clear. Logs are structured. The Qdrant team is responsive on GitHub and Discord.
**Backup/restore**: Built-in snapshot mechanism for self-hosted. Cloud offers automated backups.

## Developer Experience

- **SDKs**: Python (most mature), Rust, Go, JavaScript/TypeScript, .NET, Java.
- **API**: REST + gRPC. Clean, well-documented.
- **Filtering**: Best-in-class. Complex nested AND/OR/NOT filters, geo filters, range filters. The payload index is genuinely differentiated.
- **Frameworks**: LangChain, LlamaIndex, Haystack integrations. Less mature than Pinecone's ecosystem but improving.
- **Community**: ~22K GitHub stars. Active Discord, responsive maintainers. $50M Series B (March 2026) signals long-term viability.

## Known Issues & Sharp Edges

1. **QPS at large scale lags pgvector**: Qdrant's QPS at 50M+ vectors with standard HNSW is not the category leader. pgvectorscale (DiskANN) outperforms 11.5× at 50M vectors. Use Binary Quantization to close this gap.
2. **Ecosystem smaller than Pinecone**: Less Stack Overflow material, fewer third-party tutorials. The product changes fast — 2024 tutorials are often outdated.
3. **Hybrid search maturity**: Sparse-dense support exists but is less mature than Weaviate's BM25+vector integration.
4. **Self-hosted cluster complexity**: While simpler than Milvus, running a 3+ node Raft cluster still requires distributed systems knowledge.
5. **GPU support**: Announced for v1.12+ but not yet widely available as of mid-2026. Milvus leads on GPU acceleration.

## When to Use / When to Avoid

**Use Qdrant when**:
- You need the best metadata filtering in the industry
- You want to self-host and control costs (best value at 10M+ vectors)
- You run a Rust shop or value Rust's performance/memory safety
- You need multi-vector / ColBERT support natively
- You need GDPR/data sovereignty compliance
- Your Pinecone bill is trending above $300/month

**Avoid Qdrant when**:
- Your team has zero ops capacity and no budget concerns (Pinecone is easier)
- You need the most mature hybrid search (Weaviate wins)
- You need GPU-accelerated indexing (Milvus wins)
- You need the largest ecosystem of tutorials and Stack Overflow answers (Pinecone wins)
- You need the absolute highest QPS at 50M+ vectors without BQ (pgvectorscale wins)

## Smoke Gate Result

✅ **Passed** (2026-06-16). Collection creation with HNSW, 1,000-vector insert with metadata, and recall@10 > 0.8 all passed. Setup time: ~2 minutes with Docker.

## License

Apache-2.0

## Roster Status

**Tier A** — Strongest open-source dedicated vector DB. Retained in Tier A due to performance, filtering quality, and self-hosting viability. Watch: GPU support rollout, hybrid search maturity, ecosystem growth.
