# LanceDB

An open-source embedded vector database built on the Lance columnar format. Zero server, zero-copy, local-first — with a cloud offering in beta.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 75/100 | IVF-PQ disk-based indexing. HNSW in beta. Good recall for embedded workloads. Less mature than dedicated vector DBs |
| **Latency** | 72/100 | p95 ~20ms (disk-native). Sub-1ms for cached in-memory. Behind in-memory specialized stores but competitive for disk-based |
| **Token Economics** | 92/100 | Free (Apache 2.0). LanceDB Cloud in beta. Zero infrastructure cost for local/edge deployments |
| **Scale Behavior** | 78/100 | Disk-based indexing handles larger-than-RAM datasets. Zero-copy columnar. Automatic versioning. No horizontal scaling yet |
| **Ops Burden** | 88/100 | In-process, no server. `pip install lancedb`. Zero-copy to application memory. Minimal ops |
| **Developer Experience** | 80/100 | Clean Python/TypeScript APIs. Pydantic-based schemas. Arrow/Lance ecosystem. Smaller community than Chroma/Qdrant |
| **Data Sovereignty** | 90/100 | Fully open-source. Runs locally, edge, serverless. No cloud dependency required |
| **Composite** | **81/100** | Best for edge, local-first, and data-lake architectures. Ecosystem is maturing. Watch for HNSW GA and cloud exit beta |

## Architecture & Deployment

LanceDB is built on the Lance columnar format, designed for high-performance ML workloads. Unlike client-server vector databases, it runs in-process with zero-copy access to data. The architecture is fundamentally different from Qdrant or Weaviate.

**Key architectural features**:
- **Zero-copy columnar storage**: Data is read directly from disk into application memory without deserialization. Critical for edge and resource-constrained devices.
- **Lance format**: Unified columnar format storing vectors, text, images, and video in a single file. Designed for ML data lakes.
- **Disk-based indexing (IVF-PQ)**: Searches datasets larger than available RAM without the typical performance cliff of in-memory databases.
- **Automatic versioning**: Every write creates a new dataset version. Rollbacks and audit trails are straightforward.
- **Multi-modal**: Store embeddings of text, images, and video in the same table with typed columns.
- **Arrow-native**: Built on Apache Arrow. Integrates seamlessly with PyArrow, Polars, Pandas, and DuckDB.

**Deployment options**:
- **Embedded (in-process)**: Import as a library. No server to start. Reads/writes directly to disk. Default mode.
- **LanceDB Cloud (beta)**: Serverless cloud offering. S3-backed storage. Still in beta as of mid-2026.
- **S3 + Lambda**: Common serverless pattern. Lance files stored in S3, queried via Lambda functions.

## Key Features

- **Sub-1ms search**: For small, cached datasets. ~8,400 QPS on 1M vectors with IVF-PQ (internal benchmark, Jan 2026).
- **Larger-than-RAM datasets**: IVF-PQ indexes live on disk. Query datasets that don't fit in memory without swapping.
- **Vector + full-text hybrid**: FTS (full-text search) + vector similarity in the same query.
- **Multi-vector search**: Search across multiple vector columns in a single query.
- **Reranking**: Built-in reranking support (cross-encoder, colBERT) for second-stage retrieval.
- **Pydantic schemas**: Define tables with typed Pydantic models. Automatic validation and serialization.
- **DuckDB integration**: Query Lance tables with DuckDB SQL. Combine vector search with analytical queries.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | LanceDB Claim | Independent Result | Verdict |
|--------|--------------|-------------------|---------|
| p95 latency | 20ms | ~20ms (disk-native) | ✅ Close |
| QPS, 1M vectors (IVF-PQ) | 8,400 | Not independently verified | ⚠️ Pending |
| Scale | 1B+ vectors on object storage | Architecture supports this; real-world verification sparse | ⚠️ Pending |
| Sub-1ms search | Yes | For small cached datasets | ✅ Plausible |

### Cost at Scale (2026)

| Scale | Self-Hosted | LanceDB Cloud | Notes |
|-------|------------|-------------|-------|
| Edge/local | $0 | N/A | Free, open-source |
| 1M vectors | $0 | Beta (free) | Local disk storage only |
| 10M vectors | $0 + storage | Beta | Object storage cost (S3) |
| 100M+ vectors | S3/storage cost | Custom | Cloud pricing TBD |

**Cost model**: Open-source is free. LanceDB Cloud pricing is not yet public (beta). Self-hosted costs are storage-only (S3, local disk, etc.).

## Ops Burden

**Embedded**: Zero. `pip install lancedb` or `npm install lancedb`. No server, no port, no config.
**Cloud (beta)**: Minimal. Managed by LanceDB team. Beta pricing may change.
**S3-backed serverless**: Low. Requires S3 bucket and compute (Lambda/Functions) to query. No database to manage.

**Upgrade path**: File-format based. Lance format is versioned. Upgrades are transparent to the application.
**Debugging**: Good. Pydantic schemas catch type errors early. Arrow ecosystem provides mature debugging tools.
**Backup/restore**: File-based. Lance files are self-contained. Copy to S3, version with Git, or use standard backup tools.

## Developer Experience

- **SDKs**: Python (most mature), JavaScript/TypeScript. Rust core with language bindings.
- **API**: Pythonic. Pydantic models for schema definition. Arrow-compatible.
- **Schema**: Pydantic-based. Typed columns with automatic validation. More structured than Chroma's schema-less approach.
- **Frameworks**: LangChain, LlamaIndex integrations exist but are less mature than Chroma or Qdrant.
- **Ecosystem**: Arrow/Lance ecosystem (PyArrow, Polars, DuckDB). Good for data science and ML pipelines.
- **Documentation**: Improving. Smaller community than established alternatives. Fewer Stack Overflow answers.

## Known Issues & Sharp Edges

1. **Ecosystem immaturity**: ~5K GitHub stars. Fewer integrations, tutorials, and Stack Overflow answers than Chroma or Qdrant. The product changes fast.
2. **HNSW in beta**: The fastest index type (HNSW) is not yet stable in LanceDB. Production deployments rely on IVF-PQ which has different latency characteristics.
3. **No distributed scaling**: No horizontal scaling or clustering as of mid-2026. Roadmap targets Q3 2026. Single-node only.
4. **Multi-process limitations**: Concurrent access from multiple processes has limitations. Not ideal for multi-tenant backend services with high concurrency.
5. **Cloud offering in beta**: LanceDB Cloud is not yet GA. Pricing and SLAs are not finalized. Production reliance on beta is risky.
6. **Lower QPS than Qdrant**: 8,400 QPS vs. Qdrant's ~18,200 on comparable benchmarks. The gap is meaningful for high-throughput workloads.
7. **Smaller community**: Harder to find help on edge cases. Less production battle-testing than Chroma or Qdrant.

## When to Use / When to Avoid

**Use LanceDB when**:
- You're building edge, local-first, or desktop applications
- You need zero infrastructure — no server to run or manage
- You want to store vectors alongside raw data (text, images, video) in one format
- You need datasets larger than available RAM (disk-based indexing)
- You're already in the Arrow/Lance ecosystem (data science, ML pipelines)
- You want automatic data versioning built-in
- You're building serverless functions that query vectors from S3

**Avoid LanceDB when**:
- You need the highest query throughput (Qdrant or Redis Vector win)
- You need distributed horizontal scaling (Milvus or Qdrant cluster)
- You need the most mature ecosystem and integrations (Chroma or Qdrant win)
- You need production-grade managed cloud with guaranteed SLAs (Pinecone or Qdrant Cloud win)
- You need advanced metadata filtering (Qdrant wins)
- You need GPU acceleration (Milvus wins)
- You need the fastest HNSW search (wait for HNSW GA, or use Qdrant/Weaviate)

## Smoke Gate Result

✅ **Passed** (2026-06-16). Table creation, 1,000-vector insert, IVF-PQ index build, and recall@10 > 0.8 all passed. Setup time: ~2 minutes with `pip install lancedb`. Pydantic schema definition was straightforward.

## License

Apache-2.0

## Roster Status

**Tier A** — Best embedded vector database for edge and local-first. Retained in Tier A due to unique zero-copy architecture and multi-modal support. Watch: HNSW GA, distributed scaling roadmap, cloud exit beta, ecosystem growth.
