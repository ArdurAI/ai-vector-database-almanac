# Elasticsearch / ESRE

The enterprise search platform with native vector search. Best for teams already in the Elastic ecosystem needing hybrid text + vector + AI retrieval.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 86/100 | HNSW via Lucene. ELSER sparse model beats BM25 by 10-20%. BBQ (Better Binary Quantization) = 16× memory reduction. GPU cuVS in tech preview |
| **Latency** | 78/100 | p50 ~10-30ms. Slower than dedicated vector DBs but competitive for enterprise search workloads. DiskBBQ enables disk-backed search |
| **Token Economics** | 60/100 | Elastic Cloud: $50-300+/mo. Enterprise features gated behind paid tiers. Self-hosted: free but requires significant infra |
| **Scale Behavior** | 85/100 | Elasticsearch scales horizontally for decades. Vector search inherits this. But vector-specific scaling is newer than text search |
| **Ops Burden** | 60/100 | Elasticsearch operational complexity is well-known. Heap tuning, shard management, index mappings. Managed cloud reduces this |
| **Developer Experience** | 82/100 | Mature REST API, Kibana GUI, extensive docs. Query DSL is powerful but complex. Elastic AI Assistant for agent building |
| **Data Sovereignty** | 65/100 | AGPLv3 / Elastic License v2 / SSPL triple-licensed. Self-hosted requires license choice. BYOC available. Enterprise features paid |
| **Composite** | **74/100** | Best for existing Elastic users. The RAG platform is comprehensive but the vector layer is newer than the text search layer |

## Architecture & Deployment

Elasticsearch is a distributed search and analytics engine built on Apache Lucene. Vector search (kNN) was added as a native feature, leveraging Lucene's HNSW implementation. The Elasticsearch Relevance Engine (ESRE) bundles vector search with sparse retrieval (ELSER), reranking, and AI assistant capabilities.

**Key architectural features**:
- **Lucene HNSW**: Native dense vector fields with HNSW indexing. Integrated into Elasticsearch's distributed architecture.
- **Better Binary Quantization (BBQ)**: Default for vectors ≥384 dimensions since ES 9.1. ~16× memory reduction, <1% recall loss. 95%+ memory reduction vs float32.
- **DiskBBQ (GA 9.2)**: Disk-backed vector search. Compressed binary-quantized index in memory, full-precision vectors rescored from disk. 67% cost reduction.
- **ELSER**: Elastic Learned Sparse EncodeR. Pre-trained sparse retrieval model. Ships in-cluster, no external GPU. Beats BM25 by 10-20% on recall.
- **GPU acceleration (tech preview 9.3)**: NVIDIA cuVS integration. Up to 12× faster indexing. For GPU-heavy workloads.
- **Max dimensions**: 4,096 (Lucene constraint). This is a limitation vs. OpenSearch's 16,000 via FAISS.

**Deployment options**:
- **Self-hosted**: Download Elasticsearch, configure cluster, manage shards, heaps, and nodes. Complex but free under license terms.
- **Elastic Cloud**: Managed on AWS, Azure, GCP. Usage-based pricing. Easiest path.
- **BYOC (Enterprise)**: Run managed Elasticsearch in your own cloud account.
- **Elastic Cloud Serverless**: Newest tier. Auto-scaling, no node management.

## Key Features

- **Hybrid retrieval**: kNN vector + BM25 text + ELSER sparse in one query with Reciprocal Rank Fusion (RRF).
- **Elastic Inference API**: Generate embeddings at index and query time. Supports OpenAI, Cohere, Hugging Face, and Elastic's own models.
- **Elastic AI Assistant**: Build AI agents over Elasticsearch data with natural language. GA January 2026. MCP server import/export for Claude, Cursor, LangChain.
- **Jina AI integration**: Multilingual embedding models from Jina AI (acquired Oct 2025) built into Elastic Inference Service.
- **Retrieval chain**: Multi-stage retrieval in a single `_search` call: kNN → RRF → text reranking → diversification → rule-based pinning.
- **Semantic highlighting**: Find and surface relevant sentences by meaning rather than keyword match.
- **Kibana**: Mature GUI for data exploration, visualization, and vector search debugging.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | Elasticsearch Claim | Independent Result | Verdict |
|--------|--------------------|-------------------|---------|
| BBQ memory reduction | 95%+ vs float32 | Not independently verified | ⚠️ Pending |
| BBQ recall loss | <1% | Not independently verified | ⚠️ Pending |
| ELSER vs BM25 | +10-20% recall | Not independently verified | ⚠️ Pending |
| GPU indexing speedup | 12× (tech preview) | Not independently verified | ⚠️ Pending |
| Filtered vector throughput | 8× advantage (20M docs) | Not independently verified | ⚠️ Pending |

### Cost at Scale (2026)

| Scale | Elastic Cloud | Self-Hosted | Notes |
|-------|--------------|-------------|-------|
| 1M vectors | ~$50-150/mo | $100-200 (infra) | Small deployment |
| 10M vectors | ~$200-500/mo | $200-400 (infra) | Medium deployment |
| 100M vectors | ~$1,000-3,000/mo | $500-1,500 (infra) | Large deployment |
| Enterprise (SIEM, APM) | Custom | Custom | Full Elastic Stack |

**Cost model**: Elastic Cloud is usage-based per deployment profile. Enterprise features (LDAP, SAML, field-level security, advanced alerting) require Platinum+ tier. Self-hosted avoids license fees but requires operational expertise.

## Ops Burden

**Self-hosted**: High. Elasticsearch is notoriously operationally complex. Requires: JVM heap tuning, shard allocation strategy, index lifecycle management, cluster coordination, GC tuning. This is why managed cloud exists.
**Elastic Cloud**: Low. Managed by Elastic team. But costs scale with data volume.
**Elastic Cloud Serverless**: Very low. No node management. Auto-scaling. Higher per-unit cost but zero ops.

**Upgrade path**: Major version upgrades (8→9) require planning. Index format changes may require reindexing. Elasticsearch provides migration tools but the process is not trivial.
**Debugging**: Excellent tooling. Kibana for visualization, query profiling, index analysis. Elastic Agent Builder for debugging AI agents. `/_search` with `profile: true` for query execution analysis.
**Backup/restore**: Snapshot/restore to S3/GCS/Azure. Mature and well-tested. Elastic Cloud handles this automatically.

## Developer Experience

- **SDKs**: Official clients in Java, Python, JavaScript, Go, Ruby, PHP. Community clients for many languages.
- **API**: REST + Query DSL. Powerful but complex. steep learning curve for newcomers.
- **Query DSL**: JSON-based query language. Supports bool, match, term, range, nested, script, aggregations, and kNN. Can express almost any query but is verbose.
- **Frameworks**: LangChain, LlamaIndex integrations. Elastic AI Assistant for agent workflows.
- **GUI**: Kibana is excellent for data exploration, visualization, and debugging. Dev Tools console for ad-hoc queries.
- **Documentation**: Extensive but sprawling. The Elastic docs cover everything but finding the right page can be challenging.

## Known Issues & Sharp Edges

1. **Operational complexity**: The #1 reason teams use managed cloud. Self-hosted Elasticsearch requires dedicated expertise.
2. **License confusion**: Triple-licensed (AGPLv3 / ELv2 / SSPL). AGPLv3 requires source disclosure for network-served modifications. Most enterprises use ELv2 which forbids managed-service redistribution. This is a real constraint.
3. **Max dimensions: 4,096**: Lucene's HNSW limits vectors to 4,096 dimensions. Newer embedding models (e.g., text-embedding-3-large at 3,072) are approaching this limit. OpenSearch supports 16,000 via FAISS.
4. **Enterprise feature gating**: Security features (LDAP, SAML, field-level security, DLS) require Platinum+ tier. OpenSearch provides these for free.
5. **Vector layer maturity**: Elasticsearch's vector search is newer than its text search. Some edge cases (e.g., concurrent segment search for kNN) are still evolving.
6. **Cost at scale**: Elastic Cloud pricing scales with data volume and query load. Can become expensive for high-throughput vector workloads.
7. **JVM dependency**: Elasticsearch runs on the JVM. Heap tuning, GC pauses, and JVM upgrades are part of the operational burden.

## When to Use / When to Avoid

**Use Elasticsearch when**:
- You already use Elasticsearch for text search or log analytics and want to add vectors
- You need a comprehensive RAG platform (retrieval + reranking + AI assistant + observability) in one system
- You need ELSER's sparse retrieval model without external GPU inference
- You need enterprise security features and are willing to pay for Platinum+
- You need the Elastic ecosystem (APM, Fleet, Security SIEM) integrated with vector search
- You want semantic highlighting and advanced relevance tuning

**Avoid Elasticsearch when**:
- You need a simple, lightweight vector database (Chroma, Qdrant, or pgvector are simpler)
- You need >4,096 dimensions (OpenSearch via FAISS supports 16,000)
- You need strict open-source licensing without commercial restrictions (OpenSearch is Apache 2.0)
- You want the lowest operational burden (Pinecone or Qdrant Cloud are simpler)
- You need the fastest vector-only latency (Qdrant or Redis Vector are faster)
- You need GPU acceleration at production scale (Milvus or FAISS are further ahead)
- You need enterprise security for free (OpenSearch bundles these at no cost)

## Smoke Gate Result

✅ **Passed** (2026-06-16). Index creation with dense_vector field, HNSW mapping, document indexing, and kNN query with recall@10 > 0.8 all passed. Setup time: ~5 minutes with Docker. Hybrid query (kNN + text match) worked. Elasticsearch 8.x used for smoke gate.

## License

Elastic/AGPLv3/SSPL triple-licensed (since August 2024). Earlier versions: Elastic License v2 + SSPL.

## Roster Status

**Tier A** — Comprehensive RAG platform for existing Elastic users. Retained in Tier A due to ESRE integration, ELSER, and enterprise ecosystem. Watch: GPU acceleration GA, dimension limit increase, license adoption, vector layer maturity vs. text search layer.
