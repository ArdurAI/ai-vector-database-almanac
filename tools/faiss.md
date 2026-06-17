# FAISS

Meta's open-source library for efficient similarity search and clustering of dense vectors. The research standard and the engine inside many production vector databases.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 92/100 | Multiple index types (Flat, IVF, HNSW, RaBitQ). GPU CAGRA via cuVS. 95%+ recall achievable with correct tuning |
| **Latency** | 85/100 | CPU HNSW: competitive. GPU CAGRA: 4.7× faster search than CPU HNSW. Build time: 12.3× faster with GPU |
| **Token Economics** | 98/100 | Free (MIT). No licensing cost. Integration cost is the only expense |
| **Scale Behavior** | 90/100 | Billion-scale on single node with IVF-PQ. Multi-GPU support. Memory-mapped indices for disk-backed search |
| **Ops Burden** | 50/100 | Library, not a service. You build the system around it. Index tuning requires expertise. No built-in REST API |
| **Developer Experience** | 70/100 | Python/C++ bindings. Good for researchers and ML engineers. Not a "database" — requires integration work |
| **Data Sovereignty** | 98/100 | Fully open-source. MIT license. Runs anywhere. No vendor, no cloud dependency |
| **Composite** | **83/100** | The research standard and the engine behind Milvus, OpenSearch, and others. Choose when you need maximum control or GPU scale |

## Architecture & Deployment

FAISS is a library, not a standalone database. It provides algorithms for approximate nearest neighbor search and is integrated into many production systems (Milvus, OpenSearch, Pinecone's underlying research, etc.).

**Key architectural features**:
- **Multiple index families**: Flat (brute force), IVF (inverted file), HNSW (graph), PQ (product quantization), SQ (scalar quantization), RaBitQ (1-bit binary quantization), and GPU variants.
- **GPU acceleration via NVIDIA cuVS**: Faiss v1.10+ integrates cuVS. CAGRA graph index: 12.3× faster build, 4.7× faster search than CPU HNSW at 95% recall.
- **Memory-mapped indices**: Load indices from disk without fully resident memory. Critical for billion-scale on single machines.
- **Multi-GPU**: Distribute indices across multiple GPUs. Automatic copy management between CPU and GPU memory.
- **Quantization**: PQ, SQ, RaBitQ for memory-efficient billion-scale search. RaBitQ is the newest, providing 1-bit codes with reranking-free termination.

**Deployment patterns**:
- **Research/standalone**: `pip install faiss-cpu` or `faiss-gpu`. Direct Python usage for experiments.
- **Embedded in applications**: Link as a library in C++/Python backends. Custom REST API wrapper.
- **Inside other databases**: Milvus, OpenSearch, and others use FAISS as their ANN engine.
- **conda packages**: `faiss-cpu`, `faiss-gpu`, `faiss-gpu-cuvs` for different GPU backends.

## Key Features

- **IndexFlat**: Exact search (brute force). 100% recall. Baseline for all other indices.
- **IndexIVF**: Inverted file index. Fast build, good for batch-oriented workloads. Requires training on representative data.
- **IndexHNSW**: Hierarchical Navigable Small World. Graph-based. Fast query, high recall. No training required.
- **IndexPQ / IndexIVFPQ**: Product quantization. 4-16× memory reduction. Good for billion-scale in memory.
- **RaBitQ (v1.10+)**: 1-bit binary quantization with rotation. Extremely memory-efficient. GPU-native IVF-RaBitQ available in cuVS.
- **GPU CAGRA**: CUDA ANN Graph. State-of-the-art GPU graph index. 50× speedup claims in some configurations.
- **Auto-tuning**: `faiss.ParameterSpace` and `faiss.AutoTuneCriterion` for automatic index parameter selection.

## Benchmarking & Performance

### Published vs. Reproduced (Meta + NVIDIA cuVS, May 2025)

| Metric | FAISS/cuVS Claim | Independent Result | Verdict |
|--------|-----------------|-------------------|---------|
| CAGRA build speedup vs CPU HNSW | 12.3× | Not independently verified | ⚠️ Pending |
| CAGRA search speedup vs CPU HNSW | 4.7× | Not independently verified | ⚠️ Pending |
| IVF-PQ build speedup vs classic | 4.7× | Not independently verified | ⚠️ Pending |
| IVF-PQ search latency reduction | 8.1× | Not independently verified | ⚠️ Pending |
| Recall@10, HNSW | 95%+ | Achievable with proper tuning | ✅ Plausible |

### GPU Benchmarks (5M × 1536 embeddings)

| Index | Build Time (seconds) | Search Latency (ms) | Notes |
|-------|---------------------|---------------------|-------|
| HNSW (CPU) | 1,106.1 | 0.71 | Baseline |
| CAGRA (GPU) | 89.7 | 0.15 | 12.3× build, 4.7× search speedup |
| IVF Flat (CPU) | 24.4 | 1.98 | Baseline |
| IVF Flat (GPU cuVS) | 15.2 | 1.14 | 1.6× build, 1.7× search |
| IVF PQ (CPU) | 42.0 | 1.78 | Baseline |
| IVF PQ (GPU cuVS) | 9.0 | 0.22 | 4.7× build, 8.1× search |

## Ops Burden

**Standalone**: Moderate to high. FAISS is a library — you must build the system around it. No built-in REST API, no authentication, no replication, no backup. You write the wrapper code.
**Integration**: Low incremental ops. If embedded in Milvus or OpenSearch, the hosting system handles operations.
**GPU**: Requires NVIDIA GPU + CUDA + cuVS setup. Complex dependency chain.

**Index tuning**: Requires expertise. Parameter selection (nlist, nprobe, M, efConstruction, efSearch) significantly impacts recall and latency. Auto-tuning exists but requires representative data.
**Debugging**: Good for algorithm-level debugging. C++ core with Python wrappers. Error messages are technical. No "admin UI" — it's a library.
**Upgrade path**: Conda/pip package upgrades. API is generally stable. New index types are additive.

## Developer Experience

- **Language**: Python (primary interface), C++ (core), with some Go and Rust bindings via third parties.
- **API**: NumPy/SciPy-style. Vectors as numpy arrays. Integer IDs. Direct memory management.
- **Installation**: `conda install faiss-cpu` or `pip install faiss-cpu`. GPU variants require CUDA setup.
- **Documentation**: Good for algorithm researchers. Technical and dense. Not beginner-friendly.
- **Community**: ~39K GitHub stars. Active research community. Maintained by Meta FAIR.
- **Frameworks**: Not a direct integration target. Used via Milvus, OpenSearch, or custom wrappers.

## Known Issues & Sharp Edges

1. **Not a database**: FAISS is a library. You must build persistence, APIs, auth, replication, and monitoring yourself. Many teams underestimate this.
2. **Index tuning complexity**: Choosing the right index (IVF vs HNSW vs PQ vs CAGRA) and parameters requires deep understanding. Wrong choices yield terrible performance.
3. **GPU dependency chain**: GPU variants require CUDA, cuVS, and specific GPU architectures. Setup is complex.
4. **Dynamic updates**: Limited support. Most indices require batch building. Adding vectors incrementally is possible with HNSW but has caveats.
5. **No metadata filtering**: Pure vector search. No built-in payload filtering. Must combine with external database (Redis, PostgreSQL, etc.) for metadata queries.
6. **Research-oriented**: Documentation and API design prioritize research flexibility over production ergonomics.
7. **Memory management**: C++ core requires manual memory management in some cases. Python wrappers handle most of this but leaks can occur.

## When to Use / When to Avoid

**Use FAISS when**:
- You need maximum control over index algorithms and parameters
- You need GPU-accelerated billion-scale search
- You're building a custom vector database and need the ANN engine
- You're a researcher experimenting with new index types or quantization methods
- You need to benchmark against the standard ANN baseline
- You already use Milvus or OpenSearch (they embed FAISS)

**Avoid FAISS when**:
- You want a production vector database out of the box (use Qdrant, Weaviate, Pinecone, Milvus)
- You need metadata filtering, hybrid search, or built-in REST API (use a database)
- Your team lacks ML/algorithm expertise for index tuning
- You need the fastest time-to-production (use Chroma or Pinecone)
- You need managed cloud with zero ops (use Pinecone or Qdrant Cloud)
- You need the simplest API (use Chroma or pgvector)

## Smoke Gate Result

✅ **Passed** (2026-06-16). `IndexFlatIP` (brute force baseline) and `IndexHNSW` creation, 1,000-vector insert, and recall@10 > 0.8 all passed. Setup time: ~3 minutes with conda. No metadata/payload filtering tested (FAISS doesn't provide this natively).

## License

MIT

## Roster Status

**Tier A** — The research standard and ANN engine inside many databases. Retained in Tier A due to unmatched algorithm breadth and GPU performance. Watch: RaBitQ adoption, cuVS integration maturity, dynamic update improvements, integration into more databases.
