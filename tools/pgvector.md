# pgvector

The PostgreSQL extension that turns Postgres into a vector database. The "just use Postgres" answer for most RAG workloads under 10-50M vectors.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 85/100 | HNSW + IVFFlat. pgvectorscale (DiskANN) delivers 99% recall at 50M vectors. Standard pgvector: 95-98% recall at 1-10M vectors |
| **Latency** | 80/100 | p95 15-40ms at 10M vectors on 16-core, 64GB instance. pgvectorscale: 28ms p95 at 50M vectors, 471 QPS |
| **Token Economics** | 95/100 | Free extension. Pay only for Postgres hosting. Best TCO for teams already on PostgreSQL |
| **Scale Behavior** | 72/100 | Comfortable to 10M vectors. pgvectorscale extends to 50M+ with competitive performance. >100M requires dedicated vector DB |
| **Ops Burden** | 85/100 | Zero new operational model. Use existing Postgres tooling: backups, replication, monitoring, migrations |
| **Developer Experience** | 88/100 | SQL-native. Joins, transactions, RLS, ACID — all work with vectors. One query language for everything |
| **Data Sovereignty** | 95/100 | Runs anywhere Postgres runs. Full control. On-premise, air-gapped, any cloud provider |
| **Composite** | **84/100** | The right default for 90% of products. Use until you hit 50M+ vectors with strict latency requirements |

## Architecture & Deployment

pgvector is a PostgreSQL extension, not a standalone database. It adds `vector`, `halfvec`, and `sparsevec` data types to PostgreSQL, along with approximate nearest neighbor (ANN) indexes.

**Deployment options**:
- **Self-hosted PostgreSQL**: `CREATE EXTENSION vector;` on any Postgres 13+ instance.
- **Managed PostgreSQL**: AWS RDS, Google Cloud SQL, Azure Database for PostgreSQL, Supabase, Neon, DigitalOcean Managed PostgreSQL, Crunchy Bridge — all support pgvector as of 2026.
- **Self-hosted with pgvectorscale**: Timescale's extension adding DiskANN and Statistical Binary Quantization. Requires self-managed Postgres (NOT available on AWS RDS as of mid-2026).

**Key architectural features**:
- **HNSW index** (preferred): Graph-based ANN. Fast query, high recall. Supports concurrent inserts and incremental updates. Parallel build support (2026).
- **IVFFlat index**: Clustering-based. Faster build, compact indexes. Requires full dataset before building.
- **Exact search**: Brute-force `ORDER BY embedding <=> query`. No index needed. Slow at scale but 100% recall.
- **Iterative scan** (v0.8+): Fixes filtered vector queries. Continues searching until enough filtered results are found.
- **Half-precision vectors** (`halfvec`): ~2× storage reduction with minimal recall loss.
- **Sparse vectors** (`sparsevec`): Native sparse vector support (v0.9+). For SPLADE, BM25 sparse embeddings.
- **pgvectorscale StreamingDiskANN**: Disk-based ANN from Microsoft Research. 28× lower p95 latency and 75% less cost than Pinecone at equivalent recall.

## Key Features

- **SQL-native vector search**: `SELECT * FROM items ORDER BY embedding <-> query_embedding LIMIT 10;`. Works with `WHERE`, `JOIN`, `GROUP BY`, transactions.
- **ACID transactions**: Vector operations are part of regular PostgreSQL transactions. Rollback, consistency, isolation all apply.
- **Row-Level Security (RLS)**: Vectors inherit Postgres RLS. Multi-tenant RAG without application-level filtering.
- **Hybrid search via SQL**: Combine `ORDER BY embedding <=> query` with `tsvector` full-text search and `ts_rank` for BM25-style ranking in one query.
- **Parallel HNSW build** (2026): 30-50% faster index builds on multi-core machines.
- **pgai** (Timescale): Extension for automatic embedding sync inside Postgres. Eliminates Kafka/Debezium pipelines.
- **pgvectorscale**: StreamingDiskANN + Statistical Binary Quantization. Brings Postgres into leading-performer position at 50M+ vectors.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | pgvector Claim | Independent Result | Verdict |
|--------|---------------|-------------------|---------|
| Recall@10, 1M vectors (HNSW) | 95-98% | ~95-98% | ✅ Close |
| p95 latency, 10M vectors (HNSW) | 15-40ms | ~15-40ms on 16-core, 64GB | ✅ Close |
| pgvectorscale QPS, 50M vectors | 471 QPS | Not independently verified | ⚠️ Pending |
| pgvectorscale p95, 50M vectors | 28ms | Not independently verified | ⚠️ Pending |
| Build time, 1M vectors (parallel) | 30-50% faster | Confirmed on multi-core | ✅ Close |

### Cost at Scale (2026)

| Scale | Standard pgvector | pgvectorscale | Pinecone Equivalent |
|-------|------------------|---------------|---------------------|
| 1M vectors | $0 (extension) + Postgres cost | Same | ~$25-50/mo |
| 10M vectors | $50-100/mo (Postgres instance) | Same | ~$78-199/mo |
| 50M vectors | $200-400/mo (Postgres instance) | Same | ~$800-1,200/mo |
| 100M vectors | $400-800/mo | $400-800/mo | ~$1,500-2,500/mo |

**Note**: pgvector costs are dominated by PostgreSQL infrastructure, not licensing. If you already run Postgres, marginal cost is near zero.

## Ops Burden

**Standard pgvector**: Near-zero incremental ops. Use existing Postgres backup, replication, monitoring, and migration tools. No new service to operate.
**pgvectorscale**: Requires self-managed Postgres (not available on AWS RDS as of mid-2026). Adds one extension to manage.
**Tuning**: HNSW parameters (`m`, `ef_construction`, `ef_search`) require some tuning for optimal recall/latency. Default values are reasonable for most workloads.

**Upgrade path**: Follows PostgreSQL upgrade cycle. pgvector extension updates are simple `ALTER EXTENSION vector UPDATE;`.
**Debugging**: Excellent. Use standard Postgres tools: `EXPLAIN ANALYZE`, `pg_stat_statements`, query logs, pgAdmin, DBeaver.
**Backup/restore**: Standard Postgres `pg_dump`, `pgbackrest`, WAL archiving. No special handling needed for vectors.

## Developer Experience

- **SDKs**: Any PostgreSQL driver (psycopg2, asyncpg, pgx, JDBC, etc.). No special SDK needed.
- **API**: SQL. The most familiar interface for most developers. Join vectors with relational data in one query.
- **Frameworks**: LangChain, LlamaIndex, Haystack all support pgvector. Often the easiest integration.
- **Migrations**: Standard SQL migration tools (Alembic, Flyway, Liquibase) work for vector schemas.
- **Cloud availability**: AWS RDS, GCP Cloud SQL, Azure PostgreSQL, Supabase, Neon, DigitalOcean, Crunchy Bridge, CockroachDB. Most managed Postgres providers treat pgvector as a headline feature.

## Known Issues & Sharp Edges

1. **Scale ceiling**: Standard pgvector without pgvectorscale starts degrading above 20-50M vectors. At 50M+, Qdrant and pgvectorscale outperform standard HNSW. The exact ceiling depends on dimensions, RAM, and query patterns.
2. **Connection limits**: Subject to PostgreSQL `max_connections`. For high-concurrency vector workloads, use connection pooling (PgBouncer).
3. **GCP limitation**: Google Cloud PostgreSQL does not support HNSW for vectors > 2000 dimensions (e.g., text-embedding-3-large at 3072). Use `halfvec` or another provider.
4. **AWS RDS lacks pgvectorscale**: As of mid-2026, pgvectorscale is NOT available on AWS RDS. Teams needing DiskANN at scale must self-manage Postgres on EC2 or use another provider.
5. **No built-in embedding generation**: Unlike Weaviate or Pinecone, pgvector does not generate embeddings. You must manage your embedding pipeline externally.
6. **No native multi-tenancy**: Tenant isolation must be implemented via schema design or RLS. Less ergonomic than Weaviate's native tenant isolation.
7. **HNSW index creation stuck**: Known issue on very large datasets (pgvector issue #822). Workaround: increase `maintenance_work_mem` or use parallel build.

## When to Use / When to Avoid

**Use pgvector when**:
- You already run PostgreSQL (80% of companies do)
- Your vector dataset is under 10M vectors (the "safe zone")
- You need transactional consistency between vectors and relational data
- You want to avoid adding a new service to your infrastructure
- You need ACID compliance, joins, and SQL-native hybrid search
- You have limited DBA/ops resources and want to use existing Postgres tooling

**Avoid pgvector when**:
- Your dataset exceeds 50M vectors with strict latency requirements (use pgvectorscale or Qdrant/Milvus)
- You need extremely high write throughput (millions of vectors/hour streaming)
- You need built-in embedding generation (Weaviate or Pinecone)
- You need GPU acceleration (Milvus)
- You need the absolute lowest p99 latency in the category (Qdrant or Redis Vector)
- You need native multi-tenant shard isolation (Weaviate)
- You are on GCP with 3072-dim embeddings (HNSW not supported)

## Smoke Gate Result

✅ **Passed** (2026-06-16). `CREATE EXTENSION vector;`, table creation, 1,000-vector insert, HNSW index build, and recall@10 > 0.8 all passed. Setup time: ~1 minute on existing Postgres instance.

## License

PostgreSQL License (open-source). pgvectorscale is also open-source (Apache-2.0).

## Roster Status

**Tier A** — The default choice for teams on PostgreSQL. Retained in Tier A due to unmatched operational simplicity for existing Postgres users and strong pgvectorscale scaling. Watch: pgvectorscale availability on managed providers; scale ceiling without pgvectorscale; HNSW dimension limits on GCP.
