# Project Intent & Philosophy

## Why this almanac exists

The vector database landscape is exploding. Every week, a new "must-have" ANN library launches, a blog post claims 10x recall gains, and a vendor announces the next revolution in RAG retrieval. But **nobody independently verifies these claims**. The benchmarks are self-reported, the comparisons are marketing, and the "best tool" lists are affiliate SEO.

This almanac is the **public record of independent verification** for vector databases and retrieval systems. It exists because platform engineers need a single source of truth that answers:

- Does this vector DB actually deliver the recall@k it claims?
- What's the real ops burden of tuning HNSW parameters across 10M vectors?
- How does it fail under scale — memory explosion, index corruption, or silent recall degradation?
- What's the total cost of ownership at 100M vectors, including embedding and storage?
- Can you trust the vendor's ANN-Benchmarks numbers?

## Core principles

### 1. Frozen methodology before results

The harness, judge model, prompts, scoring rubric, and adapter contract are **fixed and published before any tool is tested**. This prevents "cherry-picking" the methodology that favors a particular vendor. If a tool doesn't fit the harness, we adapt the adapter — not the rules.

For vector databases, this means:
- Distance metrics are fixed per benchmark (cosine for ANN-Benchmarks, dot-product for BEIR where specified)
- Embedding models are frozen (e.g., `all-MiniLM-L6-v2` for standard suites)
- Index parameters are documented; if a tool auto-tunes, we document the resulting parameters
- Query batch sizes are fixed so latency comparisons are apples-to-apples

### 2. Ops-first evaluation

Most benchmarks measure recall@100 or QPS. We measure **what a platform engineer actually lives with**:
- Time from `docker pull` to first indexed query
- Dependency conflicts when installing alongside embedding pipelines
- Time to debug when recall drops 20% after a bulk insert
- Upgrade pain when version N → N+1 changes the HNSW index format
- Cost predictability at 1M → 10M → 100M vectors
- Index build time vs. query latency tradeoff — and whether you can tune it

### 3. Raw data is always published

Every benchmark run produces a JSON file with every query vector, every ground-truth neighbor, every returned neighbor, every recall@k measurement, every latency measurement, and every index parameter. These raw files are published alongside the summary. If you disagree with a ranking, you can re-analyze the data yourself.

### 4. No tool is above criticism

Every tool on the roster has been through the smoke gate. Every tool has bugs — index corruption under concurrent write, recall degradation with metadata filtering, memory explosion at high `efConstruction`. We document them honestly. A vendor relationship or sponsorship does not influence rankings. The only way a tool improves its score is by actually improving.

### 5. Living document, not a static snapshot

The almanac is updated monthly. Tools enter and exit the roster. Scores change as tools improve or degrade. The "founding edition" is a snapshot; the current edition is the truth.

## Design philosophy

### The two-bar test

Every vector database must clear two bars to justify its existence:
1. **Beat the naive baseline** on accuracy/performance (e.g., brute-force FAISS with `IndexFlatIP` must be beaten on recall@100 at the same latency, or on latency at the same recall)
2. **Beat the full-capability baseline** on cost/ops burden/complexity (e.g., Pinecone's managed service must justify itself over a self-hosted pgvector or Milvus instance)

If a tool can't do both, it has no reason to exist as infrastructure. A tool that is 2% higher recall but 10x more complex to tune than HNSW in FAISS is not worth adopting.

### The seven dimensions

We score every vector database on seven dimensions because no single number captures "good infrastructure":

| Dimension | Why it matters | How it applies to vector DBs |
|-----------|---------------|------------------------------|
| **Accuracy** | Does it retrieve the correct vectors? | Recall@k, mAP, NDCG@10 on ANN-Benchmarks / BEIR / MS MARCO |
| **Latency** | Does it respond fast enough for real-time RAG? | Query latency (p50/p95/p99), batch query throughput, index build time |
| **Token economics** | Does it cost what you expect? | Cost per 1M vectors stored, cost per 1K queries, embedding cost, egress cost |
| **Scale behavior** | What happens when you 10x the vector count? | Index build time vs. query speed tradeoff, memory footprint at 1M/10M/100M vectors, shard rebalancing behavior |
| **Ops burden** | How much of your life does it consume? | HNSW parameter tuning complexity, index maintenance overhead, upgrade pain, backup/restore complexity |
| **Developer experience** | Is it pleasant or painful to use? | SDK quality, connection pooling, error messages on dimension mismatch, hybrid search API ergonomics |
| **Data sovereignty** | Can you run it yourself? Audit it? | Self-hosting viability, on-premise deployment, hybrid search on your own hardware, GDPR/SOC 2 alignment |

### The adapter pattern

Every vector database is tested through a **VectorDBAdapter** — a frozen interface that the tool must satisfy. The adapter handles collection creation, vector ingestion, index building, querying, and teardown. This means:
- Tools are tested identically (same vectors, same queries, same distance metric)
- The adapter is the only thing that changes per tool
- New tools can be added without changing the harness
- The adapter is published and open for review

The adapter contract includes vector-specific methods:
- `create_collection(dimension, distance_metric, metadata_schema)`
- `upsert(vectors, ids, metadata)`
- `build_index(index_type, params)`
- `search(query_vector, top_k, filters)`
- `delete(ids)` / `drop_collection()`

### The canary

Every benchmark batch starts with a **no-DB baseline** (the "canary"). The canary runs the identical pipeline but with no actual index — queries return empty results. If the benchmark leaked ground-truth answers anywhere, the canary would score above zero. The canary must score exactly zero on recall — this is a hard invariant. If it doesn't, the entire batch is invalid.

## Who this is for

- **Platform engineers** evaluating which vector DB to adopt for RAG or semantic search
- **CTOs/CIOs** making build-vs-buy decisions with actual cost and ops data
- **Open-source maintainers** of ANN libraries who want independent benchmarking
- **Researchers** studying the vector database and retrieval landscape
- **Vendors** who want to improve their tools based on real evidence
- **MLEs** choosing between pgvector, Milvus, Qdrant, and Pinecone for a production pipeline

## What this is NOT

- Not a marketing site for any vector DB vendor
- Not a "best of" list based on GitHub stars or funding rounds
- Not a tutorial on how to use any specific vector database
- Not a replacement for your own workload-specific due diligence (your embedding model and dimensionality may differ)
- Not a static document that never changes

## The "Quest"

The "Platform Engineer's Quest for the Best Vector Database" is the ongoing effort to test, measure, and rank every tool on the roster. It's not a one-time effort. It's a continuous process of:
1. **Discovery** — finding new vector DBs and ANN libraries via research, community, and submissions
2. **Triage** — deciding if a tool is serious enough to enter the roster (real users, real scale claims)
3. **Smoke gate** — running every tool through an identical 3-turn scenario: create collection, insert vectors, query and verify recall
4. **Benchmark** — running ANN-Benchmarks, BEIR, MS MARCO, plus custom stress suites
5. **Publication** — publishing raw data + summary + per-tool deep-dives
6. **Iteration** — re-testing as tools update, as new benchmarks emerge, as embedding models evolve

## How to challenge a result

If you believe a ranking or score is wrong:
1. Check the **raw results JSON** — the data is public (every query vector, every neighbor returned, every recall@k)
2. Check the **adapter implementation** — the adapter code is public (did it set `ef` correctly? Did it use the right distance metric?)
3. Check the **judge prompts and benchmark parameters** — the prompts and index parameters are frozen and public
4. File an issue with a specific claim and evidence (e.g., "Your Qdrant adapter used `ef=64` but the vendor recommends `ef=128` for this dataset")
5. We'll re-run the test or update the methodology if warranted

## Governance

- **ArdurAI** maintains the almanac and runs the Quest
- **Methodology changes** require a public RFC and at least one edition cycle of notice (e.g., changing the embedding model, adding a new benchmark dataset)
- **Tool additions/removals** are decided by the triage criteria (stars, last push, community activity, seriousness, scale claims)
- **Benchmark results** are machine-generated; summaries are human-reviewed for fairness
- **Conflicts of interest** are disclosed (e.g., ArdurAI contributes to some tools on the roster); mitigation is identical harness for all

## License

Content: CC BY 4.0  
Harness code: MIT  
Raw data: CC BY 4.0
