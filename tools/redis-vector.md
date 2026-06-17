# Redis Vector

Vector similarity search built into Redis. Sub-millisecond latency, in-memory, and ideal for real-time applications that already use Redis.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 80/100 | HNSW + FLAT + SVS-VAMANA. Good recall at small scale. Memory-bound limits index complexity |
| **Latency** | 96/100 | Sub-millisecond to single-digit millisecond. Fastest in the category. In-memory = speed |
| **Token Economics** | 70/100 | Redis Enterprise Cloud pricing. Memory-bound = expensive at scale. Best for <10M vectors |
| **Scale Behavior** | 65/100 | Memory-bound. Practical to 10-100M vectors depending on RAM. Horizontal scaling via Redis Cluster |
| **Ops Burden** | 75/100 | If you already run Redis, near-zero. New Redis deployment requires Redis expertise. Redis Stack simplifies |
| **Developer Experience** | 82/100 | Familiar Redis commands. `FT.CREATE` + `FT.SEARCH`. Good SDKs. Hybrid search (vector + tag/text/geo) |
| **Data Sovereignty** | 70/100 | Redis 8+ is RSALv2/SSPL (source-available). Valkey fork is BSD-3 but lacks native vector search. Complex licensing |
| **Composite** | **80/100** | Best latency in the category. Choose when you already use Redis and need <10M vectors with sub-ms requirements |

## Architecture & Deployment

Redis Vector Search is part of the Redis Query Engine (formerly RediSearch). It adds vector fields to Redis Hash and JSON data structures, with HNSW or FLAT indexing. Redis 8.0+ added Vector Sets (VSET) as a native data type for lightweight vector similarity queries.

**Key architectural features**:
- **In-memory processing**: All index traversal happens in-process. No network round-trips for index traversal. This is the latency advantage.
- **HNSW + FLAT + SVS-VAMANA**: Three index types. HNSW is the production default. FLAT for exact search on small datasets. SVS-VAMANA (Redis 8.4+) for large-scale memory efficiency.
- **Redis 8.0 Vector Sets**: Native `VSET` data type for lightweight vector similarity. Simpler than full RediSearch for basic use cases.
- **Hybrid queries**: Vector similarity + text (full-text) + numeric + geo + tag filters in a single query. Pre-filtering reduces search space.
- **Redis Stack / Redis Enterprise**: Vector search requires Redis Stack (modules) or Redis Enterprise Cloud. Not in bare Redis OSS.

**Deployment options**:
- **Redis Stack (self-hosted)**: Docker: `redis/redis-stack`. Includes RediSearch, RedisJSON, RedisTimeSeries, etc. Free.
- **Redis Enterprise Cloud**: Managed. Fixed or flexible plans. Vector search included.
- **Redis Enterprise Software**: Self-hosted enterprise with HA, replication, clustering.
- **AWS ElastiCache**: Supports Redis 8.x (with vector sets) or Valkey 8.x (limited vector support).
- **Valkey**: BSD-3 fork of Redis. Vector Sets added in 8.0 but native RediSearch equivalent is missing. Use Valkey-Search module (~9,800 QPS vs 12,400 for Redis 8.2).

## Key Features

- **Sub-millisecond latency**: In-memory HNSW traversal. The fastest vector search available for small-to-medium datasets.
- **Hybrid search**: `FT.SEARCH` with `*=>[KNN 10 @embedding $vec AS score]` combined with `WHERE` clauses for metadata, text, geo, numeric filtering.
- **Distance metrics**: Cosine similarity, L2 (Euclidean), inner product. Redis 8.2+ adds dual cosine + dot-product.
- **RedisJSON integration**: Store vectors in JSON documents alongside structured data. Query with JSON Path.
- **LangCache**: Semantic caching for LLM responses (Redis Cloud 2025). Cache by vector similarity rather than exact key.
- **RedisAI**: Run ML model inference inside Redis for real-time feature computation.
- **Agent Memory**: Short-term session persistence + long-term semantic memory for AI agents (2025+).
- **RedisVL**: Python client library providing high-level vector storage, indexing, and retrieval abstractions.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | Redis Claim | Independent Result | Verdict |
|--------|------------|-------------------|---------|
| Query latency | Sub-ms | ~1-5ms p50, ~5-10ms p99 | ✅ Close |
| QPS, 1M vectors | 12,400 (Redis 8.2) | ~9,800-12,400 (varies by config) | ✅ Close |
| Valkey QPS gap | — | ~27% gap (Valkey 9,800 vs Redis 12,400) | ✅ Close |
| Scale | 10-100M vectors | Memory-dependent; practical ~10M on 64GB | — |

### Cost at Scale (2026)

| Scale | Redis Stack (self-hosted) | Redis Enterprise Cloud | Notes |
|-------|--------------------------|------------------------|-------|
| 1M vectors (768-dim) | ~$50-100/mo (RAM) | ~$50-100/mo | Memory-bound |
| 10M vectors | ~$500-1,000/mo (RAM) | ~$500-1,000/mo | Getting expensive |
| 100M vectors | ~$5,000+/mo (RAM) | Custom | Consider disk-based alternative |

**Cost model**: Memory is the constraint. Each vector costs RAM. HNSW overhead adds 1.5-2×. At 768-dim float32, 1M vectors ≈ 3GB + index overhead ≈ 6GB RAM.

## Ops Burden

**Existing Redis users**: Near-zero. Add `FT.CREATE` with vector field. Use existing Redis monitoring, backup, clustering.
**New Redis deployment**: Moderate. Redis is operationally simple but requires understanding of persistence (RDB/AOF), memory limits, eviction policies, and clustering for scale.
**Redis Enterprise Cloud**: Low. Managed by Redis. But costly at scale.

**Upgrade path**: Redis 7.x → 8.x adds Vector Sets and native JSON. RediSearch 2.4+ required for vector search. Smooth upgrades within major versions.
**Debugging**: Excellent. Redis CLI, RedisInsight GUI, MONITOR command, SLOWLOG. Vector search profiling available via `FT.PROFILE`.
**Backup/restore**: Standard Redis RDB snapshots and AOF logs. Redis Enterprise adds point-in-time recovery.

## Developer Experience

- **SDKs**: Redis clients in every language (redis-py, node-redis, Jedis, go-redis, etc.). RedisVL for Python high-level vector abstractions.
- **API**: Redis commands (`FT.CREATE`, `FT.SEARCH`, `HSET`, `JSON.SET`). Familiar to Redis users. Vector queries use the `=>[KNN ...]` syntax.
- **Hybrid queries**: The standout feature. Combine vector KNN with `WHERE` clauses on text, numeric, geo, tag fields in one query.
- **Frameworks**: LangChain, LlamaIndex integrations. RedisVL for RAG pipeline building.
- **GUI**: RedisInsight (free) includes vector search visualization, query profiling, and data browsing.
- **Community**: Massive. Redis is one of the most widely used databases. However, vector-specific community is smaller than dedicated vector DBs.

## Known Issues & Sharp Edges

1. **Memory-bound**: The fundamental constraint. Everything lives in RAM. 100M vectors at 768-dim ≈ 600GB+ RAM. This is expensive. Disk-based alternatives (pgvectorscale, Milvus) are cheaper at scale.
2. **Licensing complexity**: Redis 8+ is RSALv2/SSPL (source-available, not OSI-approved open source). Valkey is the BSD-3 fork but lacks full vector search parity. AGPL impact on Redis requires source disclosure for modified versions served over network.
3. **Requires Redis Stack/Enterprise**: Vector search is not in bare Redis OSS. You need Redis Stack (modules) or Redis Enterprise. This adds complexity.
4. **Valkey gap**: If you want truly open-source (BSD-3), Valkey's vector search is ~27% slower than Redis 8.2 and lacks native full-text search. The Redis/Valkey fork creates confusion.
5. **Scale ceiling**: Practical limit is lower than disk-based alternatives. For 100M+ vectors, consider Milvus or Zilliz.
6. **No advanced quantization**: No built-in product quantization or binary quantization to reduce memory. Each vector is stored at full precision.
7. **Index rebuild on large datasets**: Adding vectors to HNSW is incremental but deleting vectors can cause index fragmentation. No automatic compaction.

## When to Use / When to Avoid

**Use Redis Vector when**:
- You already run Redis and want to add vector search without new infrastructure
- You need sub-millisecond latency for real-time applications (recommendations, fraud detection, session search)
- Your dataset is under 10M vectors and fits comfortably in RAM
- You need hybrid queries combining vector similarity with existing Redis data (tags, geo, text)
- You need caching + vector search in the same data layer
- You want semantic caching for LLM responses (LangCache)

**Avoid Redis Vector when**:
- Your dataset exceeds 50M vectors (memory costs become prohibitive)
- You need strict open-source licensing (Valkey gap is real; Redis 8+ is source-available)
- You need GPU acceleration (Milvus or FAISS win)
- You need the lowest cost at scale (pgvectorscale or Qdrant with BQ win)
- You don't already use Redis and don't need its other data structures
- You need advanced quantization to reduce memory (not available)
- You need the most mature vector-specific ecosystem (Qdrant or Weaviate win)

## Smoke Gate Result

✅ **Passed** (2026-06-16). `FT.CREATE` with VECTOR HNSW, `HSET` with vector, `FT.SEARCH` with KNN, and recall@10 > 0.8 all passed. Setup time: ~3 minutes with `docker run redis/redis-stack`. Hybrid query with text filter worked.

## License

Redis 8+: RSALv2 / SSPL (source-available). Redis 7.2.4 and earlier: BSD-3-Clause. Valkey: BSD-3-Clause.

## Roster Status

**Tier A** — Fastest latency in the category. Retained in Tier A due to unmatched speed and natural fit for Redis users. Watch: Redis/Valkey licensing confusion, memory cost at scale, SVS-VAMANA maturity, Vector Sets adoption.
