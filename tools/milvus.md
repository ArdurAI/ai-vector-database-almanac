# Milvus

The open-source workhorse for billion-scale vector search. GPU-accelerated, cloud-native, and operationally complex. Zilliz Cloud is the managed wrapper.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 88/100 | Multiple index types (HNSW, IVF, DiskANN, CAGRA GPU). Tuned correctly, recall is excellent. Tuning requires expertise |
| **Latency** | 78/100 | p50 ~6ms, p99 ~18-50ms at scale. GPU CAGRA can be 50× faster than HNSW. CPU path is competitive but not class-leading |
| **Token Economics** | 70/100 | Self-hosted: free but requires significant infra. Zilliz Cloud: from $65/mo. Best value at 100M+ vectors where complexity pays off |
| **Scale Behavior** | 92/100 | Built for 100M+ vectors. Storage-compute separation. Horizontal scaling. GPU acceleration. The scale leader |
| **Ops Burden** | 55/100 | K8s-native with etcd, MinIO, Pulsar/Kafka. Complex. Overkill for <10M vectors. Requires dedicated infra team |
| **Developer Experience** | 75/100 | Good SDKs (Python, Go, Java, Node.js). Attu GUI is excellent. API is clean but the ecosystem is more "enterprise" than "developer-friendly" |
| **Data Sovereignty** | 85/100 | Open-source (Apache-2.0), self-hosted, BYOC, Zilliz Cloud. LF AI & Data graduated project |
| **Composite** | **77/100** | The scale king. Choose when you have 100M+ vectors and a team to operate it. Overkill for small workloads |

## Architecture & Deployment

Milvus is built for billion-scale vector datasets from day one. It separates storage and compute into microservices: proxy, query node, data node, index node, and coordinator. This architecture enables true elastic scaling but adds significant operational complexity.

**Core components**:
- **Proxy**: Request routing and load balancing
- **Query Node**: Handles search queries
- **Data Node**: Manages data insertion and persistence
- **Index Node**: Builds indexes asynchronously
- **Coordinator**: Metadata and cluster management (requires etcd)
- **Storage**: MinIO/S3 for object storage, etcd for metadata
- **Message Queue**: Pulsar or Kafka for streaming data ingestion

**Deployment options**:
- **Milvus Lite**: In-process, no server. For prototyping and small datasets (<100K vectors). pip install.
- **Docker (standalone)**: Single-node for development and small production. Simpler but not HA.
- **Kubernetes (distributed)**: Production deployment. Helm charts available. Requires K8s expertise + etcd + MinIO.
- **Zilliz Cloud**: Fully managed Milvus. From $65/mo. Three-layer tiered storage (memory → SSD → S3).
- **Zilliz Cloud Enterprise**: BYOC, dedicated resources, premium SLAs.

**Key architectural features**:
- **Storage-compute separation**: Data lives in object storage; compute scales independently.
- **GPU acceleration**: CAGRA (from NVIDIA RAPIDS cuVS) for GPU indexing. Up to 50× faster than CPU HNSW in some benchmarks.
- **Multiple index types**: HNSW, IVF_FLAT, IVF_PQ, IVF_SQ8, DiskANN, GPU_CAGRA, GPU_IVF_FLAT, GPU_IVF_PQ, SCANN, Flat.
- **Tiered storage**: Hot data in memory, warm in SSD, cold in S3. Up to 87% lower storage costs.
- **JSON Shredding / JSON Path indexing**: Metadata filtering up to 100× faster.
- **Hybrid BM25 + vector search**: Full-text + dense vector in one query.

## Key Features

- **GPU CAGRA indexing**: NVIDIA CUDA-accelerated graph index. Milvus 2.4+ introduced this. Milvus 2.6 added hybrid GPU-CPU architectures (GPU for graph construction, CPU for retrieval).
- **Index Build Level**: Zilliz Cloud feature. Balance recall, performance, and storage automatically. Choose precision, balanced, or capacity profiles.
- **Multi-tenancy**: Database/collection-level isolation.
- **RBAC**: Fine-grained role-based access control.
- **Attu**: Open-source GUI for Milvus management. Excellent for visualizing collections, indexes, and query performance.
- **Milvus 2.6.x on Zilliz Cloud GA** (January 2026): Cloud-native multi-layer storage, Index Build Level, JSON Shredding.
- **Zilliz Cloud Vortex format**: S3-based vector format for lake-native storage. 100B+ scale claims.
- **Cardinal engine**: Zilliz proprietary engine claiming 10× performance over open-source Milvus.

## Benchmarking & Performance

### Published vs. Reproduced

| Metric | Milvus/Zilliz Claim | Independent Result | Verdict |
|--------|--------------------|-------------------|---------|
| GPU CAGRA speedup | 50× vs CPU HNSW | Not independently verified at same hardware | ⚠️ Pending |
| Scale | Billions of vectors | Architecture supports this; real-world verification sparse | ✅ Plausible |
| p50 latency, 1M vectors | ~6ms | ~6-12ms | ✅ Close |
| p99 latency, 10M vectors | ~18ms | ~18-50ms (varies by config) | ✅ Close |
| JSON filtering | 100× faster | Not independently verified | ⚠️ Pending |

### Cost at Scale (2026 pricing)

| Scale | Zilliz Cloud | Self-Hosted (K8s) | Notes |
|-------|-------------|-------------------|-------|
| 1M vectors | ~$65/mo | $100-200/mo (infra) | Managed saves ops cost at small scale |
| 10M vectors | ~$200-400/mo | $200-400/mo (infra) | Break-even around here |
| 100M vectors | ~$800-1,500/mo | $500-1,000/mo (infra) + SRE time | Self-hosted wins on pure cost |
| 1B vectors | Custom Enterprise | $2,000-5,000/mo (infra) | Milvus territory; others struggle |

**Cost drivers**: Zilliz Cloud uses tiered storage + CU (compute unit) billing. Self-hosted costs are infrastructure + significant SRE time.

## Ops Burden

**Milvus Lite / Docker standalone**: Low to moderate. Setup in ~15 minutes. Good for development and small scale.
**Kubernetes distributed**: High. Requires:
- Kubernetes cluster (EKS/GKE/AKS or on-prem)
- etcd for metadata (3+ nodes for HA)
- MinIO or S3 for object storage
- Pulsar or Kafka for message streaming
- Helm chart deployment and ongoing management
- Understanding of Milvus's specific K8s resource requirements

**Zilliz Cloud**: Low. Handles all operations. The primary reason to use Zilliz.

**Upgrade path**: Complex for distributed deployments. Cross-version compatibility requires careful planning. Milvus v2.6.14+ had 40+ bug fixes for RBAC backup/restore and cross-version upgrade compatibility.
**Debugging**: Attu GUI helps. Logs are distributed across microservices, making debugging harder than single-node databases. Query tracing is available but complex.
**Backup/restore**: Built-in but requires S3 configuration. RBAC backup/restore had bugs in v2.6.x that were fixed in patches.

## Developer Experience

- **SDKs**: Python (most mature), Go, Java, Node.js, C#, Ruby, Rust.
- **API**: gRPC + REST. Clean, well-documented.
- **Attu**: Excellent GUI for database management. Standout feature for visual learners.
- **Frameworks**: LangChain, LlamaIndex, Haystack. Good integrations.
- **Schema**: Collection-based with field definitions. Flexible but requires upfront design.
- **Community**: ~42K GitHub stars. Largest among open-source vector DBs. Active but can be enterprise-focused.

## Known Issues & Sharp Edges

1. **Operational complexity**: The #1 reason teams avoid Milvus. Running a distributed Milvus cluster requires K8s expertise, etcd management, and MinIO configuration. At small scale, this is overkill.
2. **Overkill for small workloads**: If you have <10M vectors, Milvus is like using Cassandra for a thousand-user app. Qdrant or pgvector are better fits.
3. **GPU dependency for top performance**: CAGRA requires NVIDIA GPUs. Not all environments have GPU access.
4. **Distributed debugging difficulty**: Logs spread across proxy, query, data, index nodes. Tracing a slow query requires understanding the entire microservice topology.
5. **Index tuning complexity**: Multiple index types (HNSW, IVF, DiskANN, GPU variants) require expertise to select and tune. Default settings are often not optimal.
6. **Zilliz Cloud vs. open-source gap**: Cardinal engine and some optimizations are proprietary to Zilliz Cloud. Open-source Milvus may lag behind managed offering.

## When to Use / When to Avoid

**Use Milvus when**:
- You have 100M+ vectors and need horizontal scaling
- You have a dedicated infrastructure/DevOps team (5+ people) or use Zilliz Cloud
- You need GPU-accelerated indexing for massive datasets
- You need the most index type options for workload-specific tuning
- You need tiered storage (hot/warm/cold) for cost optimization at billion scale
- You need strong enterprise features (RBAC, multi-tenancy, audit logging)
- You already run Kubernetes heavily

**Avoid Milvus when**:
- You have <10M vectors (Qdrant, pgvector, or Pinecone are simpler)
- Your team has <2 DevOps engineers and you don't want managed Zilliz Cloud
- You need sub-5ms p50 at small scale (Qdrant or Redis Vector are faster)
- You need the fastest time-to-production (Pinecone or Qdrant Cloud)
- You need the most mature hybrid search (Weaviate wins)
- You want a single-binary deployment (Qdrant wins)

## Smoke Gate Result

✅ **Passed** (2026-06-16). Collection creation, 1,000-vector insert with metadata, and recall@10 > 0.8 passed with Milvus Lite. Setup time: ~5 minutes. Distributed K8s setup was not tested in smoke gate.

## License

Apache-2.0 (Milvus open-source). Zilliz Cloud and Cardinal engine are proprietary.

## Roster Status

**Tier A** — The billion-scale leader. Retained in Tier A due to unmatched scale capabilities and GPU acceleration. Watch: operational complexity vs. Zilliz Cloud value proposition; gap between open-source and managed features.
