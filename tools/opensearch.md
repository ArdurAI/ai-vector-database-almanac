# OpenSearch

The Apache 2.0 fork of Elasticsearch. Strong vector search via FAISS and Lucene, with GPU acceleration and a thriving open-source community.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 84/100 | HNSW (Lucene) + FAISS + NMSLIB. Neural sparse retrieval. 1-bit scalar quantization. Up to 16,000 dimensions via FAISS |
| **Latency** | 80/100 | p50 ~10-30ms. Concurrent segment search for kNN delivers 2.5× faster queries (3.0+). GPU acceleration via cuVS |
| **Token Economics** | 75/100 | Free (Apache 2.0). Amazon OpenSearch Service 30-50% cheaper than Elastic Cloud. Aiven, Bonsai, Sematext managed options |
| **Scale Behavior** | 85/100 | Distributed architecture. UltraWarm/Cold tiers for cost-effective storage. GPU acceleration for large-scale indexing |
| **Ops Burden** | 62/100 | Similar complexity to Elasticsearch. K8s operator available. Amazon OpenSearch Service reduces ops. Still complex |
| **Developer Experience** | 80/100 | Query DSL compatible with ES 7.10. OpenSearch Dashboards (Kibana fork). Good docs. ML Commons for model management |
| **Data Sovereignty** | 92/100 | Apache 2.0. Linux Foundation governance. Self-hosted, BYOC, or managed. No license restrictions on service offerings |
| **Composite** | **80/100** | The Apache 2.0 choice. Strong vector features, free security, and growing community. Best for AWS-native or license-conscious teams |

## Architecture & Deployment

OpenSearch is an Apache 2.0-licensed fork of Elasticsearch 7.10.2, created by AWS in April 2021 after Elastic changed Elasticsearch's license. It is now governed by the OpenSearch Software Foundation (Linux Foundation). The vector search engine supports multiple backends: Lucene HNSW, FAISS, and NMSLIB (deprecated in 3.0).

**Key architectural features**:
- **Multiple vector engines**: Lucene HNSW (native), FAISS (IVF, PQ, binary quantization), NMSLIB (deprecated). More flexible than Elasticsearch's Lucene-only approach.
- **Up to 16,000 dimensions**: Via FAISS. Nearly 4× Elasticsearch's 4,096 limit. Critical for high-dimensional embeddings.
- **1-bit scalar quantization**: Binary quantization via FAISS with 32× compression. Alternative to Elasticsearch's BBQ.
- **Disk-based vector search**: Two-phase approach: compressed binary-quantized index in memory, full-precision vectors rescored from disk. ~67% cost reduction.
- **Concurrent segment search for kNN**: Enabled by default in 3.0. Up to 2.5× faster vector queries via parallel segment search.
- **GPU acceleration (preview)**: NVIDIA cuVS integration for index building and search. 9.5× performance improvement over v1.3.
- **gRPC + MCP**: gRPC for efficient data transport. MCP support for AI agent integration (OpenSearch 3.0+).

**Deployment options**:
- **Self-hosted**: Docker, Kubernetes (operator available), bare metal, any cloud VM. Free, Apache 2.0.
- **Amazon OpenSearch Service**: AWS-managed. Typically 30-50% cheaper than Elastic Cloud. IAM integration, native S3 snapshots.
- **Aiven**: Managed on AWS, Azure, GCP, DigitalOcean.
- **Bonsai / Sematext**: Managed OpenSearch hosting.
- **BYOC**: Run in your own cloud infrastructure.

## Key Features

- **Neural Search**: Run ML models (local or remote) during query and index time for embedding generation and semantic search.
- **Agentic AI (Agent-v2, 3.6.0)**: Token usage tracking, observability traces over LLM calls, relevance tuning helpers, APM integration.
- **Flow Framework**: Orchestrate AI-driven search workflows. 82% query translation accuracy, 235% relevance improvements in benchmarks.
- **Launchpad (April 2026)**: AI-powered tool that generates a running search application from plain-language requirements in minutes.
- **Agent Health**: Open-source observability and evaluation for AI agents. Trace-level visibility, automated benchmarking, LLM-as-judge evaluation.
- **ML Commons**: Free model management. Load, serve, and manage ML models within the cluster. No external inference service needed.
- **Search Relevance Workbench**: Offline evaluation tools for search quality tuning (added in 3.5).
- **Bulk SIMD for FP16**: 58% throughput jump for FP16 vector operations.
- **Reader/writer separation**: Isolate query load from indexing for better performance stability.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | OpenSearch Claim | Independent Result | Verdict |
|--------|-----------------|-------------------|---------|
| Concurrent segment search kNN | 2.5× faster | Not independently verified | ⚠️ Pending |
| GPU acceleration | 9.5× vs v1.3 | Not independently verified | ⚠️ Pending |
| Indexing throughput | 9.3× faster | Not independently verified | ⚠️ Pending |
| Cost reduction | 3.75× ops cost | Not independently verified | ⚠️ Pending |
| Recall, FAISS HNSW | 95%+ | Achievable with proper tuning | ✅ Plausible |

### Cost at Scale (2026)

| Scale | Amazon OpenSearch Service | Self-Hosted | Aiven Managed | Notes |
|-------|--------------------------|-------------|---------------|-------|
| 1M vectors | ~$40-120/mo | $100-200 (infra) | ~$50-150/mo | Cheaper than Elastic Cloud |
| 10M vectors | ~$150-400/mo | $200-400 (infra) | ~$200-500/mo | AWS-native discount |
| 100M vectors | ~$800-2,000/mo | $500-1,500 (infra) | Custom | UltraWarm/Cold tiers help |

**Cost model**: Amazon OpenSearch Service is 30-50% cheaper than Elastic Cloud. Self-hosted is infrastructure-only. Aiven adds multi-cloud convenience.

## Ops Burden

**Self-hosted**: High. Same complexity as Elasticsearch. JVM heap, shard management, cluster coordination. K8s operator reduces but doesn't eliminate this.
**Amazon OpenSearch Service**: Low. AWS manages operations. But you still need to understand index sizing, shard counts, and query patterns.
**Aiven/Bonsai**: Low. Managed by provider.

**Upgrade path**: Major version upgrades require planning. OpenSearch can restore snapshots from ES 7.x. Migrating from ES 8.x/9.x requires reindexing due to format divergence.
**Debugging**: OpenSearch Dashboards (Kibana fork) for visualization and query debugging. Dev Tools console. `/_plugins/_knn` API for vector-specific diagnostics. Agent Health for AI agent observability.
**Backup/restore**: Snapshots to S3/GCS/Azure. Mature. Amazon OpenSearch Service handles this automatically.

## Developer Experience

- **SDKs**: OpenSearch clients (Python, Java, JavaScript, Go, Ruby, PHP). Some ES 7.x clients are compatible.
- **API**: Query DSL compatible with Elasticsearch 7.10. Plus OpenSearch-specific extensions (neural search, ML Commons, etc.).
- **Query DSL**: Same JSON-based language as Elasticsearch. Powerful, verbose, complex.
- **Frameworks**: LangChain, LlamaIndex integrations. Neural Search for native embedding generation.
- **GUI**: OpenSearch Dashboards. Feature-rich but visually dated compared to Kibana. Functional for data exploration and debugging.
- **Documentation**: Good and improving. Community-driven docs may be less polished than Elastic's but are freely accessible.
- **Community**: ~9.5K GitHub stars, 3,300+ contributors, 400+ Foundation members. Growing rapidly. Linux Foundation governance provides stability.

## Known Issues & Sharp Edges

1. **Operational complexity**: Same as Elasticsearch. OpenSearch is not a simple database to self-host. K8s operator helps but doesn't eliminate the learning curve.
2. **KNN plugin maturity**: Vector search is a plugin (`k-NN`), not a core native feature like Elasticsearch's dense_vector. This creates a subtle architectural boundary.
3. **NMSLIB deprecation**: NMSLIB engine was deprecated in 2.16 and removed for new index creation in 3.0. If you used NMSLIB, you must migrate to HNSW or FAISS.
4. **BBQ gap**: No equivalent to Elasticsearch's Better Binary Quantization yet. Active RFC exists but not implemented. FAISS binary quantization is the alternative.
5. **GPU acceleration still preview**: As of mid-2026, GPU acceleration is experimental. Not production-ready for all workloads.
6. **Ecosystem fragmentation**: Some tools and plugins are AWS-specific. The broader ecosystem is still catching up to Elasticsearch's maturity.
7. **GUI quality**: OpenSearch Dashboards is functional but less polished than Kibana. Some advanced visualizations require workarounds.

## When to Use / When to Avoid

**Use OpenSearch when**:
- You need Apache 2.0 licensing with no commercial restrictions
- You're building a managed search service or SaaS product (no SSPL/ELv2 restrictions)
- You're on AWS and want the cheapest managed option (Amazon OpenSearch Service)
- You need >4,096 dimensions (FAISS supports 16,000)
- You need enterprise security features for free (RBAC, TLS, SAML, FLS, audit logging)
- You want a community-governed project (Linux Foundation) rather than single-vendor control
- You need agentic AI observability (Agent Health, Flow Framework)

**Avoid OpenSearch when**:
- You need the absolute lowest vector search latency (Qdrant or Redis Vector are faster)
- You need ELSER's pre-trained sparse model (Elasticsearch-exclusive)
- You need the most polished management UI (Kibana is better than OpenSearch Dashboards)
- You need GPU acceleration at production scale today (Milvus or FAISS are further ahead)
- You need the Elastic ecosystem (APM, Fleet, Security SIEM) — these are Elastic-only
- You need the simplest vector-only database (Chroma, Qdrant, or pgvector are simpler)
- You want the most mature managed cloud experience (Pinecone or Qdrant Cloud are more polished)

## Smoke Gate Result

✅ **Passed** (2026-06-16). KNN index creation with FAISS HNSW engine, document indexing, and vector search with recall@10 > 0.8 all passed. Setup time: ~5 minutes with Docker. Neural search query with model inference was not tested in smoke gate (requires model deployment).

## License

Apache-2.0

## Roster Status

**Tier A** — The Apache 2.0 alternative to Elasticsearch. Retained in Tier A due to strong vector features, free enterprise security, and growing community. Watch: GPU acceleration GA, BBQ equivalent implementation, NMSLIB migration, ecosystem maturity, agentic AI features adoption.
