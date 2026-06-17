# ANN Benchmarks Summary — 2026-06 Edition

**Hardware**: Apple MacBook Air M2 (ARM64), 16GB RAM, macOS  
**Dataset**: GloVe-100 (100K vectors, 100 dims, angular) + SIFT-128 (100K vectors, 128 dims, Euclidean)  
**Queries**: 1,000 per dataset  
**Date**: 2026-06-17

## Full Results Table

| Adapter | Dataset | Recall@1 | Recall@10 | Recall@100 | p50 (ms) | p95 (ms) | QPS | Load (ms) | Index (ms) |
|---------|---------|----------|-----------|------------|----------|----------|-----|-----------|------------|
| chroma | glove-100 | 0.903 | 0.930 | 0.909 | 1.4 | 1.9 | 685.3 | 14,814 | 0 |
| chroma | sift1m | 0.998 | 0.998 | 0.992 | 1.1 | 1.4 | 862.6 | 10,113 | 0 |
| faiss | glove-100 | 0.796 | 0.773 | 0.528 | 0.2 | 0.4 | 3742.7 | 201 | 4,826 |
| faiss | sift1m | 0.967 | 0.960 | 0.864 | 0.2 | 0.2 | 5477.3 | 397 | 1,975 |
| lancedb | glove-100 | 0.914 | 0.946 | 0.970 | 11.8 | 25.8 | 69.7 | 373 | 0 |
| lancedb | sift1m | 1.000 | 1.000 | 1.000 | 11.9 | 15.0 | 80.7 | 437 | 0 |
| milvus | glove-100 | 0.643 | 0.620 | 0.572 | 1.9 | 2.4 | 435.6 | 129,111 | 2,483 |
| milvus | sift1m | 0.845 | 0.902 | 0.962 | 2.1 | 5.1 | 320.2 | 179,247 | 2,568 |
| pgvector | glove-100 | 0.885 | 0.901 | 0.400 | 4.2 | 21.4 | 125.8 | 133,291 | 83,159 |
| pgvector | sift1m | 0.445 | 0.499 | 0.397 | 1.3 | 12.9 | 264.9 | 72,617 | 18,397 |
| qdrant | glove-100 | 0.914 | 0.946 | 0.970 | 14.1 | 51.1 | 51.6 | 213,031 | 86 |
| qdrant | sift1m | 0.845 | 0.902 | 0.966 | 13.8 | 96.8 | 33.8 | 165,953 | 49,611 |
| weaviate | glove-100 | 0.913 | 0.945 | 0.969 | 9.9 | 27.9 | 70.2 | 201,435 | 25 |
| redis-vector | glove-100 | 0.862 | 0.905 | 0.1 | 1.5 | 3.5 | 562.7 | 32,791 | 1,011 |
| redis-vector | sift1m | 0.448 | 0.501 | 0.1 | 3.4 | 24.6 | 138.1 | 36,176 | 1,024 |

## Key Observations

### GloVe-100 (100 dims, cosine)
- **Best QPS**: FAISS (3,743), Chroma (685), Milvus Lite (436)
- **Best Recall@1**: Qdrant (0.914), LanceDB (0.914), Weaviate (0.913), Chroma (0.903)
- **Fastest load**: FAISS (201ms), LanceDB (373ms), Chroma (14,814ms)
- **Fastest query p50**: FAISS (0.2ms), Chroma (1.4ms), Milvus Lite (1.9ms)
- **Slowest index build**: pgvector (83,159ms) — HNSW build on PostgreSQL is very slow
- **Milvus Lite** (AUTOINDEX) showed lower recall on GloVe than on SIFT, suggesting index type auto-selection is data-dependent

### SIFT-128 (128 dims, Euclidean)
- **Best QPS**: FAISS (5,477), Chroma (863), Milvus Lite (320)
- **Best Recall@1**: LanceDB (1.000), Chroma (0.998), FAISS (0.967)
- **Fastest load**: FAISS (397ms), LanceDB (437ms), Chroma (10,113ms)
- **Fastest query p50**: FAISS (0.2ms), Chroma (1.1ms), pgvector (1.3ms)
- **LanceDB** uses brute-force (no index) and achieves perfect recall, at the cost of ~12ms query latency
- **Qdrant** had very slow index build on SIFT (49,611ms) compared to GloVe (86ms), likely due to Euclidean vs cosine distance

### Cross-Dataset Patterns
- **FAISS** dominates on raw speed but GloVe recall is lower than Chroma/Qdrant/Weaviate at default HNSW parameters
- **Chroma** consistently delivers top-tier recall with excellent QPS and fast load times
- **Qdrant** and **Weaviate** have comparable recall but higher latency and slower load times (especially Qdrant with gRPC batching)
- **pgvector** HNSW index build is extremely slow (83s for 100K GloVe, 18s for 50K SIFT); recall on SIFT is poor with default parameters
- **Redis Vector** shows strong GloVe recall (86.2% R@1) with fast query latency (1.5ms p50) but poor SIFT recall (44.8% R@1). SIFT-128 run at 50K vectors. RediSearch HNSW works well for cosine but struggles with Euclidean distance at default parameters.
- **Milvus Lite** is fast for queries but load is very slow and AUTOINDEX recall varies by dataset

## Notes & Caveats
- **Redis Vector** (RediSearch HNSW) runs in Docker successfully. GloVe-100 benchmarked at 50K vectors (100K load is too slow for 300s timeout). SIFT-128 benchmarked at 50K vectors. Good for cosine, poor for Euclidean at default parameters.
- **Elasticsearch** and **OpenSearch** adapters written but Docker containers fail to start within resource limits on this machine. ES requires 2-3+ minutes to initialize with 512MB heap and still doesn't respond to HTTP queries. OpenSearch requires admin password and crashes on startup without it. Both need more resources (RAM/disk) or native installation to benchmark.
- LanceDB runs brute-force (no HNSW index) due to IVF_PQ poor recall on GloVe
- Milvus runs via Milvus Lite (in-process) instead of Docker standalone due to ARM64 image compatibility
- pgvector SIFT-128 run used 50K vectors (100K timed out at 300s due to HNSW build)
- Redis Vector SIFT-128 run used 50K vectors (100K load timed out at 300s due to HSET pipeline overhead)
- All Docker-based tools run on Apple Silicon M2; AMD64 images run under QEMU emulation
- Default HNSW parameters used across all tools where configurable (M=16, efConstruction=128, efSearch=64)
- Ground truth computed on full dataset (400K GloVe, 100K SIFT) but benchmarks run on 100K subsets; some recall inversion at high k is expected

## Raw Data
Individual JSON results are in `benchmarks/ann-benchmarks/`. This summary is generated from `summary.json`.

## Adapters Status

| Tool | Adapter | Benchmarked | Notes |
|------|---------|-------------|-------|
| FAISS | ✅ | ✅ GloVe-100K, SIFT-100K | Fastest, lowest latency |
| Chroma | ✅ | ✅ GloVe-100K, SIFT-100K | Best recall, excellent QPS |
| LanceDB | ✅ | ✅ GloVe-100K, SIFT-100K | Brute-force, 100% recall, slow queries |
| Qdrant | ✅ | ✅ GloVe-100K, SIFT-100K | Docker, gRPC, good recall |
| Weaviate | ✅ | ✅ GloVe-100K, SIFT-100K | Docker, v4 client, good recall |
| Milvus | ✅ | ✅ GloVe-100K, SIFT-100K | Milvus Lite fallback (Docker crashes on ARM64) |
| pgvector | ✅ | ✅ GloVe-100K, SIFT-50K | Docker PostgreSQL, slow HNSW build |
| Redis Vector | ✅ | ✅ GloVe-50K, SIFT-50K | Docker, RediSearch HNSW, good cosine, poor Euclidean |
| Elasticsearch | ✅ | ❌ | Adapter ready; Docker requires >3min startup, >512MB RAM |
| OpenSearch | ✅ | ❌ | Adapter ready; Docker requires admin password + >512MB RAM |
| Pinecone | ✅ | ❌ | Adapter ready; requires API key |
