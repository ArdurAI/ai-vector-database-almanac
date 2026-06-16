# Testing & Benchmarking

How the almanac tests vector databases, what the harness does, how scoring works, and how to reproduce results.

## Table of Contents

1. [The Three Benchmark Types](#the-three-benchmark-types)
2. [The Seven Dimensions](#the-seven-dimensions)
3. [The Harness Architecture](#the-harness-architecture)
4. [The Canary](#the-canary)
5. [Standard Benchmarks](#standard-benchmarks)
6. [PlatformOps Custom Benchmarks](#platformops-custom-benchmarks)
7. [Stress Suite](#stress-suite)
8. [Cross-Category Integration Tests](#cross-category-integration-tests)
9. [Scoring](#scoring)
10. [Reproducibility](#reproducibility)
11. [Failure Mode Taxonomy](#failure-mode-taxonomy)

---

## The Three Benchmark Types

Every vector database is tested across three types of benchmarks:

| Type | Purpose | Frequency |
|------|---------|-----------|
| **Standard benchmarks** | Verify vendor claims with published ANN/retrieval suites | Every benchmark run |
| **PlatformOps custom benchmarks** | Test ops reality: setup, index tuning, stress, failure modes | Every benchmark run |
| **Cross-category integration tests** | Test how vector DBs work in a full RAG stack | Quarterly |

## The Seven Dimensions

Every tool is scored 0-100 on each dimension. The final score is a weighted average, but the per-dimension scores are always published.

| Dimension | Weight | What it measures | How it's tested |
|-----------|--------|-----------------|-----------------|
| **Accuracy** | 25% | Does it retrieve the correct neighbors? | ANN-Benchmarks (recall@k), BEIR (NDCG@10, mAP), MS MARCO (MRR@10) |
| **Latency** | 15% | Query speed, batch throughput, index build time | Instrumented measurements; p50, p95, p99 query latency; vectors/second build rate |
| **Token Economics** | 15% | Cost per 1M vectors, per query, embedding cost | Standardized workloads; $/1M vectors/month, $/1K queries, measured egress |
| **Scale Behavior** | 15% | What happens at 1M → 10M → 100M vectors? | Load tests; saturation curves; memory footprint vs. vector count; shard rebalancing |
| **Ops Burden** | 15% | Index tuning complexity, upgrade pain, maintenance | Measured setup time; smoke-gate sweep; HNSW parameter tuning iterations; backup/restore test |
| **Developer Experience** | 10% | SDK quality, error messages, hybrid search API, docs | Structured rubric; connection pooling tests; error message clarity on dimension mismatch |
| **Data Sovereignty** | 5% | Self-hosting viability, audit trails, on-premise deployment | Feature matrix; GDPR/SOC 2 mapping; air-gapped deployment test |

### Why these weights?

The weights reflect what a platform engineer actually cares about. Accuracy (recall) is the most important — a vector DB that returns wrong neighbors is useless regardless of how fast or cheap it is. But ops burden is nearly as important because a tool that requires a PhD in HNSW parameter tuning is not worth a 2% recall gain.

Weights are reviewed annually. Changes require an RFC and a public comment period.

## The Harness Architecture

```
┌─────────────────────────────────────────┐
│  VectorDBAdapter (frozen contract)      │
│  ├── setup(dimension, metric)           │
│  ├── load(vectors, ids, metadata)       │
│  ├── build_index(type, params)          │
│  ├── await_ready() → async barrier      │
│  ├── search(query, top_k, filters)      │
│  ├── delete(ids)                        │
│  └── teardown() → cleanup, measure     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Telemetry Collector                    │
│  ├── query latency (p50/p95/p99)       │
│  ├── index build time & throughput      │
│  ├── memory & CPU usage during ops      │
│  ├── recall@k and NDCG computation        │
│  ├── error rate & failure mode taxonomy │
│  └── ops notes (setup friction, tuning) │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Grading Pipeline                       │
│  ├── Exact recall@k (vs. brute force)    │
│  ├── BEIR/MS MARCO judge (frozen)       │
│  ├── Second pass (confidence < 0.7)     │
│  └── Failure mode taxonomy              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Results Publisher                      │
│  ├── Raw JSON (per query, per run)     │
│  ├── Summary tables (per tool)          │
│  ├── Recall-latency curve plots         │
│  └── Cross-verification analysis        │
└─────────────────────────────────────────┘
```

### The `await_ready()` barrier

This is where async-ingestion designs get their cost measured instead of hidden. Many vector databases (Milvus with background compaction, Qdrant with optimization, Elasticsearch with merge operations) claim "fast" write paths because the actual index build happens in the background. The `await_ready()` barrier forces the tool to finish all background indexing before the query is run, so the true index build latency is measured.

### The Telemetry Collector

Every adapter call is instrumented:
- **Latency**: `time.monotonic()` around every `search()` call; p50, p95, p99 computed across all queries
- **Index build time**: Time from first `upsert()` to `await_ready()` returning
- **Throughput**: Queries per second (QPS) at batch size 1 and batch size 100
- **Memory**: `psutil` or container metrics for memory usage during index build and query
- **CPU**: CPU utilization during index build and query
- **Recall**: `recall@k` computed against brute-force ground truth for ANN-Benchmarks; NDCG@10 for BEIR
- **Errors**: Every exception, timeout, index corruption, or unexpected result is logged with full traceback
- **Ops notes**: Human observations about HNSW tuning friction, documentation clarity, parameter auto-tuning quality

## The Canary

The first run of every batch is the **no-DB baseline** through the identical pipeline. The canary creates a collection but builds no index and runs queries against an empty store. If the benchmark leaked ground-truth answers anywhere, the canary would score above zero on recall.

**Canary rules**:
- The canary must score exactly **0.000** on recall@k for all answerable queries
- The canary must return **empty results** for all search queries
- If the canary fails, the entire batch is invalid and must be rerun
- The canary run is published alongside the real results
- The canary adapter is a no-op: `setup()` creates a stub, `search()` returns `[]`, `teardown()` cleans up

## Standard Benchmarks

### ANN-Benchmarks

The primary suite for measuring approximate nearest neighbor performance.

| Dataset | Vectors | Dimensions | Metric | What it tests |
|---------|---------|------------|--------|---------------|
| **SIFT** | 1M | 128 | Euclidean | Classic ANN benchmark: balanced recall vs. speed |
| **GloVe-100** | 1.2M | 100 | Cosine | Real-world text embeddings, cosine similarity |
| **GloVe-200** | 1.2M | 200 | Cosine | Higher dimensionality, harder index problem |
| **Deep1B (subset)** | 10M | 96 | Euclidean | Large-scale deep learning embeddings |
| **Fashion-MNIST** | 60K | 784 | Euclidean | High-dimensional dense vectors (image) |

**Metrics captured**:
- `recall@1`, `recall@10`, `recall@100` vs. brute-force ground truth
- Query latency p50/p95/p99 at each recall target
- Index build time and memory footprint
- Index size on disk

**Published vs. reproduced**:

Every standard benchmark ranking ships a table:

| Tool | Published Claim | Our Result | Delta | Verdict |
|------|----------------|------------|-------|---------|
| Tool A | 98% recall@100 on SIFT | 96% recall@100 | -2% | ✅ Close |
| Tool B | "Fastest QPS on GloVe" | 3rd of 8 | — | ⚠️ Misleading |
| Tool C | No claim | 94% recall@100 | N/A | — |

### BEIR (Benchmarking IR)

Zero-shot information retrieval benchmark using vector databases as retrievers.

| Dataset | Domain | Metric | What it tests |
|---------|--------|--------|---------------|
| **MSMARCO** | Passage retrieval | NDCG@10, MRR@10 | Dense passage retrieval quality |
| **TREC-COVID** | Scientific | NDCG@10 | Biomedical domain adaptation |
| **NQ (Natural Questions)** | QA | NDCG@10 | Question-answering retrieval |
| **FiQA** | Financial | NDCG@10 | Financial domain QA |
| **SCIDOCS** | Scientific | NDCG@10 | Citation-based scientific search |
| **ArguAna** | Argumentation | NDCG@10 | Argument similarity |

**How it works**: The adapter loads the BEIR corpus, embeds it with the frozen embedding model, indexes it, and runs the queries. We compute NDCG@10 and compare to the published dense retrieval baseline.

### MS MARCO Passage Retrieval

Large-scale passage retrieval benchmark.

- **Corpus**: 8.8M passages
- **Queries**: 6,980 dev queries
- **Metrics**: MRR@10, recall@1000, R-precision
- **What it tests**: End-to-end dense retrieval quality at scale, filtering support, reranking integration

### Embedding model specification

All benchmarks use a **frozen embedding model** to ensure fair comparison:
- Default: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, cosine)
- BEIR suite: `sentence-transformers/msmarco-distilbert-base-v4` (768-dim, dot-product)
- Model versions are pinned and recorded in `results.json` metadata
- If a tool requires its own embedding model (e.g., for hybrid search), the adapter must document this and the results are annotated

## PlatformOps Custom Benchmarks

### Setup experience

**Measured**:
- Time from `docker pull` / `pip install` to first indexed query
- Number of dependency conflicts when installing alongside embedding pipelines (e.g., `torch`, `transformers`, `onnxruntime`)
- Time to resolve dependency conflicts
- Number of undocumented steps required (e.g., "you must manually set `vm.max_map_count` for Elasticsearch")
- Time to find the answer in the docs when stuck (e.g., "how do I set `efConstruction` in this tool?")

**Scored on**:
- Sub-5 minutes: 90-100
- 5-30 minutes: 70-89
- 30-60 minutes: 50-69
- 60+ minutes or unresolved: 0-49

### Smoke gate

Every vector database must pass an identical 3-turn scenario before entering the roster:

```
Turn 1: Create a collection with dimension 384 and cosine metric
Turn 2: Insert 1,000 vectors with metadata (title, category, timestamp)
Turn 3: Query with a vector and verify recall@10 > 0.8 against brute-force ground truth
```

**Pass criteria**:
- No crashes, no silent failures, no index corruption
- Results must be deterministic (same query vector → same top-k neighbors, same distances)
- Tool must handle the basic case without workarounds (no manual index parameter tuning required to pass)
- Metadata must be retrievable alongside vectors

**What the smoke gate surfaced** (vector DB-specific examples):
- **Index corruption**: Tool builds HNSW but returns random results after 1,000 vectors
- **Distance metric mismatch**: Tool claims cosine but implements normalized dot-product, causing silent recall drops
- **Memory explosion**: Tool allocates 4GB for 1,000 vectors due to default `max_elements` being 1B
- **Async indexing lies**: Tool claims "instant" writes but recall@10 = 0.1 until background compaction finishes (caught by `await_ready()`)
- **Dimension rigidity**: Tool cannot change dimension without full cluster restart
- **Metadata filtering bugs**: Filter `category == "tech"` returns vectors from all categories

### Stress suite

| Test | What it does | What it reveals |
|------|-------------|---------------|
| **Contradiction storms** | Insert vectors with identical embeddings but contradictory metadata, then filter | Metadata filtering correctness, index consistency |
| **Near-duplicate floods** | Insert 100K nearly identical vectors (cosine similarity > 0.99) | Deduplication quality, index bloat, recall degradation |
| **Temporal paradoxes** | Insert vectors with timestamps, delete old ones, query with new ones | Delete propagation correctness, tombstone handling, index compaction quality |
| **Concurrent writers** | Multiple threads/agents upserting simultaneously | Race conditions, locking, eventual consistency, index corruption |
| **Kill-the-backing-store** | Crash the database/service mid-index-build | Recovery, data integrity, index rebuild time, whether vectors are lost |
| **Cost-runaway** | Run the tool at maximum scale (1M → 10M vectors) for 1 hour | Cost predictability, billing accuracy, memory leak detection, OOM behavior |
| **Distance metric torture** | Run same dataset with cosine, Euclidean, dot-product | Metric correctness, whether results are consistent across metrics |
| **Hybrid search stress** | Run sparse+dense hybrid queries at high load | Sparse index stability, reranking latency, fusion score correctness |

### Upgrade path

**Tested**:
- Can you upgrade from version N to N+1 without reindexing everything?
- Are there breaking changes in the index format (e.g., HNSW index v1 → v2)?
- Is there a migration guide for index parameters?
- Does the tool maintain backward compatibility for the SDK/API?
- Do old vectors still query correctly after upgrade, or is recall affected?

### Debugging experience

**Tested**:
- When the tool fails (e.g., recall drops), can you find out why in <5 minutes?
- Are error messages clear and actionable? (e.g., "dimension mismatch: expected 384, got 768" vs. "internal error: code 500")
- Is there a debug mode or verbose logging for index operations?
- Are there known issues documented for index corruption, memory leaks, or recall degradation?
- Can you trace the execution path (query planner, index selection, shard routing)?

## Cross-Category Integration Tests

These tests run quarterly and check how vector databases work together in a realistic RAG stack:

| Integration | What it tests | Tools involved |
|-------------|-------------|---------------|
| **Agent + Vector DB + LLM** | Full RAG pipeline: agent embeds query, retrieves from vector DB, feeds to LLM | Agent framework, vector DB, model serving |
| **Vector DB + Observability** | Can you trace retrieval latency and recall in production? | Vector DB, observability tool (e.g., Langfuse, LangSmith) |
| **Vector DB + Data Processing** | Embedding pipeline → vector DB → search, end-to-end | Data processing tool, vector DB |
| **Security + Vector DB** | Do guardrails filter toxic queries before embedding? | Security tool, vector DB |
| **MCP + Vector DB** | Can an MCP server expose the vector DB to agents? | MCP implementation, vector DB |

## Scoring

### Per-dimension scoring

Each dimension is scored 0-100 using a rubric. The rubric is published before any scoring happens.

**Example: Accuracy rubric**

| Score | Criteria |
|-------|----------|
| 90-100 | ≥95% recall@100 on ANN-Benchmarks; NDCG@10 within 2% of SOTA on BEIR; no critical failures in stress suite |
| 80-89 | 90-95% recall@100; NDCG@10 within 5% of SOTA; minor failures in stress suite |
| 70-79 | 85-90% recall@100; NDCG@10 within 10% of SOTA; some stress suite failures (metadata filtering bugs) |
| 60-69 | 80-85% recall@100; frequent stress suite failures (near-duplicate recall degradation) |
| 50-59 | 75-80% recall@100; significant reliability issues (index corruption under concurrent write) |
| 0-49 | <75% recall@100 or fundamentally unreliable (recall drops below 50% at scale) |

**Example: Latency rubric**

| Score | Criteria |
|-------|----------|
| 90-100 | p95 < 5ms at 1M vectors; index build < 5 min for 1M vectors |
| 80-89 | p95 < 20ms at 1M vectors; index build < 15 min for 1M vectors |
| 70-79 | p95 < 50ms at 1M vectors; index build < 30 min for 1M vectors |
| 60-69 | p95 < 100ms at 1M vectors; index build < 60 min for 1M vectors |
| 50-59 | p95 < 200ms at 1M vectors; or index build > 60 min for 1M vectors |
| 0-49 | p95 > 200ms or index build > 2 hours for 1M vectors |

### Composite score

The composite score is a weighted average of the seven dimensions:

```
Composite = (Accuracy × 0.25) + (Latency × 0.15) + (TokenEconomics × 0.15) +
            (ScaleBehavior × 0.15) + (OpsBurden × 0.15) + (DevEx × 0.10) +
            (DataSovereignty × 0.05)
```

The composite is used for ranking, but the per-dimension scores are always published. A tool with a high composite but low ops burden score is a warning sign (e.g., excellent recall but requires manual HNSW tuning for every dataset).

### Confidence intervals

Every score is reported with a confidence interval computed from the standard error across runs. If the intervals overlap between two tools, the difference is not statistically significant. For ANN-Benchmarks, we report confidence intervals on recall@k and latency separately.

## Reproducibility

### How to reproduce a benchmark

1. Clone the benchmark harness repo (published separately)
2. Check out the exact commit used for the run (recorded in the results JSON)
3. Install the exact dependencies (lockfile is published)
4. Download the exact dataset and embedding model checkpoint (SHA-256 recorded)
5. Run the harness with the same adapter, same seed, same distance metric
6. Compare your results to the published results

### What is frozen

| Element | How it's frozen | Where to find it |
|---------|---------------|------------------|
| Embedding model | Pinned model name and version | `results.json` metadata |
| Distance metric | Fixed per dataset | `methodology/benchmark-harness.md` |
| Judge prompts | SHA-256 hash | `methodology/benchmark-harness.md` |
| Control variables | Documented values | `results.json` metadata |
| Random seeds | Published integer | `results.json` metadata |
| Adapter code | Published in harness repo | Separate repo |
| Test workloads | Published JSON files | `benchmarks/` directory |
| Batch sizes | Fixed (1 and 100) | `methodology/benchmark-harness.md` |

### What is NOT frozen (and why)

| Element | Why it changes | How we handle it |
|---------|---------------|------------------|
| Tool versions | Vector DBs update | We re-run benchmarks for new versions; old results are archived |
| Provider pricing | Cloud pricing changes | Cost is computed at runtime using current pricing; historical results are annotated |
| Hardware | We may upgrade machines | Hardware spec (CPU, RAM, GPU) is recorded in `results.json`; results are hardware-specific |
| Index parameters | Some tools auto-tune | We document the effective parameters in the results; if auto-tuning changes, we annotate |

## Failure Mode Taxonomy

Every failure is classified into a taxonomy. This helps identify patterns across tools and categories.

| Category | Failure Modes | Vector DB Examples |
|----------|--------------|--------------------|
| **Setup** | `install_failed`, `dependency_conflict`, `config_error`, `missing_env_var`, `docs_incomplete` | Missing `vm.max_map_count`, CUDA version mismatch for GPU indices, Docker not available for containerized tools |
| **Ingestion** | `write_timeout`, `write_crash`, `data_loss`, `index_corruption`, `async_lag` | HNSW corruption under concurrent write, memory OOM during bulk insert, async indexing claiming "done" but recall still low |
| **Query** | `query_timeout`, `query_crash`, `wrong_result`, `missing_recall`, `irrelevant_result` | Recall@10 drops to 0.1 after delete, distance metric producing wrong ordering, metadata filter ignored silently |
| **Scale** | `throughput_degradation`, `memory_leak`, `cpu_spike`, `connection_pool_exhaustion`, `rate_limit_hit` | Memory leak during 10M vector insert, QPS drops 50% at 5M vectors, managed service rate limiting queries |
| **Ops** | `upgrade_breaking`, `undocumented_behavior`, `debug_opacity`, `community_unresponsive` | HNSW index format change requiring full rebuild, `ef` parameter meaning different across versions, no logs for recall degradation |
| **Security** | `prompt_injection`, `data_leakage`, `pii_exposure`, `jailbreak`, `tool_spoofing` | Vector DB leaking metadata in error messages, embedding model exposing PII in vector space, unauthorized collection access |
| **Integration** | `mcp_noncompliant`, `a2a_noncompliant`, `auth_failure`, `protocol_mismatch` | MCP server not exposing search correctly, hybrid search API incompatible with LangChain, authentication token expiry |

## License

Content: CC BY 4.0  
Code: MIT
