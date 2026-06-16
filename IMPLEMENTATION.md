# Implementation Guide

How the vector database almanac is built, how to add a tool, how to update an edition, and how the data pipeline works.

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [The Data Pipeline](#the-data-pipeline)
3. [Adding a New Vector Database](#adding-a-new-vector-database)
4. [Updating an Edition](#updating-an-edition)
5. [The Roster JSON Schema](#the-roster-json-schema)
6. [Directory Conventions](#directory-conventions)
7. [Building the Adapter](#building-the-adapter)
8. [Automation](#automation)

---

## Repository Structure

```
ai-vector-database-almanac/
├── README.md                          # Project overview + roster at a glance
├── INTENT.md                          # Philosophy, design principles, governance
├── IMPLEMENTATION.md                  # This file
├── TESTING.md                         # Benchmark methodology, harness details
├── TROUBLESHOOTING.md                 # Common issues, debugging, FAQ
├── CONTRIBUTING.md                    # How to contribute
├── architecture.md                    # Stack architecture + test philosophy
├── SETUP.md                           # How to push to GitHub
├── .gitignore
│
├── editions/                          # Monthly editions
│   └── 2026-06.md                   # Founding edition
│
├── benchmarks/                        # Benchmark results (rolling)
│   ├── ann-benchmarks/
│   ├── beir/
│   ├── ms-marco/
│   └── stress-suite/
│
├── methodology/
│   └── benchmark-harness.md         # Detailed harness spec
│
├── data/
│   └── roster.json                  # Machine-readable catalog (80+ tools)
│
├── tools/                             # Per-tool deep-dive pages
│   ├── pinecone.md
│   ├── qdrant.md
│   ├── milvus.md
│   └── (populated as deep-dives are written)
│
└── assets/                            # Charts, diagrams, screenshots
    ├── recall-latency-curve-2026-06.png
    ├── memory-vs-scale-2026-06.png
    └── (populated by editions)
```

## The Data Pipeline

The almanac data flows through four stages:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Discovery      │────▶│  Triage         │────▶│  Research       │────▶│  Publication    │
│  (find tools)   │     │  (decide entry) │     │  (deep dive)    │     │  (write edition) │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Stage 1: Discovery

Tools are discovered through:
- **Monthly research swarm**: 8-10 parallel agents search for new vector databases and ANN libraries
- **Community submissions**: Issues, PRs, email, social media, HN threads, Reddit r/vectordatabases
- **Vendor announcements**: Funding rounds, product launches, major releases (e.g., Milvus 3.0, pgvector 0.8.0)
- **GitHub trending**: New repos with significant star growth in the ANN/vector search space
- **Conference talks**: NeurIPS, SIGMOD, VLDB papers on approximate nearest neighbor search
- **Benchmark leaderboards**: New entrants on ANN-Benchmarks with competitive recall/latency curves

### Stage 2: Triage

A tool enters the roster if it meets ALL of these criteria:
1. **Seriousness**: Not a toy/demo. Must have a real use case, real users, or real funding. Must support at least 1M vectors or have a clear path to it.
2. **Activity**: Last push or release within 6 months. Exceptions for "stable/mature" tools (e.g., FAISS has slower release cadence but is widely used).
3. **Documentation**: Must have a README, docs, or at least a landing page explaining what it does, how to index, and how to query.
4. **Accessibility**: Must be accessible to test (open source, free tier, or evaluation license available). Must support standard distance metrics (cosine, Euclidean, dot-product at minimum).
5. **Scope**: Must fit the category definition. A general-purpose database with a vector extension (e.g., PostgreSQL + pgvector) qualifies; a pure full-text search engine with no vector support does not.

A tool is **excluded** if:
- It's a fork of FAISS/Annoy/HNSW with no meaningful divergence
- It's a thin wrapper around another vector DB with no added value
- It has no users, no community, and no evidence of real-world use at scale
- It requires an enterprise-only license with no evaluation path
- It does not support standard vector operations (index, search, delete)

### Stage 3: Research

For each new tool, we collect:
- Name, type (Vector DB, ANN Library, Managed Service), license, language, GitHub URL, stars
- Last push date, release cadence, latest version
- Supported distance metrics, index types (HNSW, IVF, PQ, SCANN, etc.), metadata filtering capabilities
- Hybrid search support (sparse-dense, BM25 + vectors, reranking)
- Known bugs and sharp edges (from smoke gate): index corruption, memory leaks, recall drops
- Community health (issues, PRs, maintainer responsiveness, Discord/Slack activity)
- Cost model: self-hosted (hardware requirements), managed (price per 1M vectors, price per query), open-source (free but ops cost)

This data is stored in `data/roster.json` and summarized in the edition.

### Stage 4: Publication

The edition is a markdown file that includes:
- Landscape at a glance table (recall@100 vs. latency scatter plot summary)
- Per-tool findings: new index types, recall improvements, breaking changes
- New tools added and tools removed
- Notable releases and acquisitions (e.g., Pinecone serverless, Milvus Zilliz Cloud)
- Quest diary (what was tested this month: which benchmarks, which tools, what surfaced)
- Cost tracking: price changes in managed services

## Adding a New Vector Database

### Step 1: Verify the tool meets triage criteria

Check: seriousness, activity, documentation, accessibility, scope. For vector DBs specifically:
- Does it support at least one standard index type (HNSW, IVF, graph-based, tree-based)?
- Does it support metadata filtering (at least simple key-value)?
- Can it handle 100K+ vectors in the free tier or local build?

### Step 2: Add to the roster JSON

Edit `data/roster.json` and add the tool to the `vector-databases` category:

```json
{
  "name": "ToolName",
  "type": "Vector DB | ANN Library | Managed Service",
  "license": "License",
  "region": "Region",
  "tier": "A|B|C",
  "notes": "One-line description and key differentiators (index types, hybrid search, scale claims)"
}
```

**Tier assignment rules**:
- **Tier A**: Market leader, widest adoption, or strongest recall/latency tradeoff. Must be actively maintained and have real production usage at 1M+ vectors. Examples: Pinecone, Qdrant, Weaviate, Milvus, pgvector.
- **Tier B**: Solid option, actively maintained, but not the market leader. Good for specific use cases (e.g., embedded, multi-modal, specific cloud). Examples: Chroma, LanceDB, Vald, Marqo.
- **Tier C**: Niche, early-stage, or specialized. Worth knowing about but not a default choice. Examples: new ANN libraries with promising algorithms but limited ecosystem, experimental GPU indices.

### Step 3: Update the edition

Add the tool to the appropriate section in `editions/YYYY-MM.md`. If the tool is Tier A, add it to the roster-at-a-glance table in the README.

### Step 4: Update the category README (if applicable)

If your repo has cross-references or sub-categories, update relevant `categories/<subcategory>/README.md`.

### Step 5: Run the smoke gate

Before the tool is officially "in," it must pass the smoke gate (see TESTING.md). The smoke gate for vector DBs is:
1. Create a collection with dimension 384 and cosine metric
2. Insert 1,000 vectors with metadata
3. Query and verify recall@10 > 0.8 against brute-force ground truth

If it fails, document the failure in the edition and assign it to Tier C with a note about the blocker.

### Step 6: Build the adapter

Write a `VectorDBAdapter` for the tool (see Building the Adapter below). The adapter is required for the tool to be benchmarked.

## Updating an Edition

### Monthly update checklist

```
□ Check for new tools (discovery phase)
□ Triage new tools (add to roster or reject)
□ Update metadata for existing tools (stars, last push, releases, new versions)
□ Flag tools for removal (dead/abandoned, no commits in 12 months)
□ Run smoke gate for new tools
□ Run benchmark updates for re-tested tools (ANN-Benchmarks, BEIR, MS MARCO)
□ Update cost tracking for managed services (pricing changes)
□ Draft the edition markdown
□ Update README roster-at-a-glance
□ Update per-tool deep-dive pages if new data surfaced
□ Commit and push
```

### Edition markdown template

```markdown
# Edition YYYY-MM — [Title]

*Research conducted YYYY-MM-DD. [Context about this month: new releases, acquisitions, benchmark breakthroughs].*

## The landscape at a glance

| Tool | Tier | Recall@100 (SIFT1M) | Query Latency p95 | Index Build Time | Cost/Mo (1M vectors) |
|------|------|---------------------|-------------------|------------------|----------------------|

## [Theme] — What's new this month

### Tier A roster
[table with per-tool metrics]

### Findings
- [Index algorithm breakthroughs or regressions]
- [Managed service pricing changes]
- [New hybrid search capabilities]
- [Community health shifts]

## Quest diary — [Month] [Year]

- [what was tested: which tools, which benchmarks, what surfaced]
- [adapter bugs found and fixed]
- [stress suite results: memory leaks, recall degradation, etc.]

## Cost tracker

| Tool | Price/Mo (1M vectors) | Change | Notes |
|------|----------------------|--------|-------|

## Coming next month

[what's planned: new tools to test, new benchmarks to add, methodology updates]

## License
Content is licensed CC BY 4.0.
```

## The Roster JSON Schema

```json
{
  "meta": {
    "name": "Vector Databases & RAG Infrastructure Almanac Roster",
    "version": "YYYY-MM",
    "generated_at": "ISO-8601 timestamp",
    "total_tools": number,
    "categories": number,
    "research_method": "description"
  },
  "categories": {
    "vector-databases": {
      "name": "Vector Databases & ANN Libraries",
      "description": "Vector databases, approximate nearest neighbor libraries, and managed vector search services",
      "estimated_total": number,
      "tools": [
        {
          "name": "Tool Name",
          "type": "Vector DB | ANN Library | Managed Service",
          "license": "License",
          "region": "Region",
          "tier": "A|B|C",
          "notes": "Description"
        }
      ]
    }
  }
}
```

**Field definitions**:
- `name`: The tool's common name. Use the name the tool calls itself (e.g., "Qdrant", "FAISS", "Pinecone").
- `type`: What kind of tool is it? (e.g., "Vector DB", "ANN Library", "Managed Service", "Database Extension")
- `license`: The primary license. Use SPDX identifiers where possible. For managed services, use "Proprietary".
- `region`: Where the tool is primarily developed (US, EU, China, Global, etc.)
- `tier`: A, B, or C (see tier rules above)
- `notes`: One-line description with key differentiators. Keep under 100 chars. Mention index types, hybrid search, or standout features.

## Directory Conventions

### `editions/`
- One file per month: `YYYY-MM.md`
- Never delete old editions. The history is part of the record.
- New editions are appended; old editions are never rewritten.

### `data/`
- `roster.json` is the single source of truth for the tool catalog.
- It is machine-generated from the research process.
- It should be valid JSON at all times.

### `benchmarks/`
- `ann-benchmarks/`: One file per run: `<tool>-<dataset>-<date>.md` and `.json` (e.g., `qdrant-sift-2026-06.json`)
- `beir/`: One file per run: `<tool>-<dataset>-<date>.md` and `.json`
- `ms-marco/`: One file per run: `<tool>-<date>.md` and `.json`
- `stress-suite/`: One file per run: `<tool>-stress-<date>.md` and `.json`
- Raw data is never deleted. It is the audit trail.

### `tools/`
- One file per tool: `<name>.md`
- Contains deep-dive analysis: setup experience, index parameters tested, benchmark results, bug notes, comparison with peers, cost analysis
- Populated as deep-dives are written (not all tools have a page immediately)

### `assets/`
- Images, charts, diagrams referenced by editions and benchmarks
- Named descriptively: `recall-latency-qdrant-2026-06.png`, `memory-vs-scale-2026-06.png`, `landscape-2026-06.png`

### `methodology/`
- The benchmark harness specification
- Frozen before any results are generated
- Changes require an RFC and a public announcement
- Includes: embedding models used, distance metrics per dataset, batch sizes, warm-up procedures, index parameter documentation rules

## Building the Adapter

When a new vector database is added to the roster and is ready for benchmarking, a `VectorDBAdapter` must be built. The adapter is the bridge between the tool's API and the harness's fixed interface.

### The VectorDBAdapter contract

```python
class VectorDBAdapter:
    def setup(self, dimension: int, distance_metric: str) -> None:
        """Install, configure, and start the tool. Create a collection."""
        pass
    
    def load(self, vectors: list[list[float]], ids: list[str], metadata: list[dict]) -> None:
        """Ingest the vectors into the collection."""
        pass
    
    def build_index(self, index_type: str, params: dict) -> None:
        """Build the ANN index with specified parameters."""
        pass
    
    def await_ready(self) -> None:
        """Wait for async indexing to complete. Measure lag."""
        pass
    
    def search(self, query_vector: list[float], top_k: int, filters: dict = None) -> list[dict]:
        """Run the query and return the top-k results with IDs and distances."""
        pass
    
    def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID."""
        pass
    
    def teardown(self) -> None:
        """Clean up, drop collection, measure resource usage."""
        pass
```

### Adapter rules

1. The adapter must be **pure** — it should not modify the tool's behavior, only interface with it. Do not implement custom reranking or post-processing.
2. The adapter must be **documented** — every step should be explainable in plain English. Index parameters must be logged.
3. The adapter must be **reproducible** — running it twice on the same machine should produce the same setup and same index parameters.
4. The adapter must be **isolated** — it should not depend on other tools' adapters. Use separate collections or namespaces per tool.
5. The adapter code is **published** in the benchmark harness repo (separate from the almanac repo).

### Example adapter (pseudocode)

```python
class QdrantAdapter(VectorDBAdapter):
    def __init__(self, config):
        self.config = config
        self.collection_name = "almanac-test"
    
    def setup(self, dimension=384, distance_metric="cosine"):
        subprocess.run(["docker", "run", "-d", "--name", "qdrant-test", "-p", "6333:6333", "qdrant/qdrant"])
        self.client = QdrantClient(url="http://localhost:6333")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
        )
    
    def load(self, vectors, ids, metadata):
        points = [
            PointStruct(id=id, vector=vec, payload=meta)
            for vec, id, meta in zip(vectors, ids, metadata)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
    
    def build_index(self, index_type="hnsw", params=None):
        # Qdrant auto-builds HNSW on upsert; we log the effective params
        info = self.client.get_collection(self.collection_name)
        log.info(f"Index config: {info.config.params.vectors.hnsw_config}")
    
    def await_ready(self):
        # Wait for index to be fully optimized
        while True:
            info = self.client.get_collection(self.collection_name)
            if info.status == CollectionStatus.GREEN:
                break
            time.sleep(0.5)
    
    def search(self, query_vector, top_k=10, filters=None):
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filters
        )
    
    def delete(self, ids):
        self.client.delete(collection_name=self.collection_name, points_selector=ids)
    
    def teardown(self):
        self.client.delete_collection(self.collection_name)
        subprocess.run(["docker", "stop", "qdrant-test"])
        subprocess.run(["docker", "rm", "qdrant-test"])
```

### Adapter test checklist

Before submitting a new adapter, verify:
- [ ] `setup()` works on a fresh machine (no hidden dependencies)
- [ ] `load()` ingests 100K vectors in under 5 minutes
- [ ] `build_index()` completes and logs effective parameters
- [ ] `await_ready()` terminates (does not hang on async indexing)
- [ ] `search()` returns results with IDs and distances in the expected format
- [ ] `delete()` removes vectors without corrupting the index
- [ ] `teardown()` cleans up completely (no orphaned containers, no disk bloat)
- [ ] The adapter produces deterministic results (same query → same top-k, same distances)

## Automation

### Monthly update cron

The monthly update is run by a scheduled job:
- **Trigger**: `cron` expression `0 7 15 * *` (monthly, 15th at 7:00 AM)
- **Action**: Runs a research agent to discover new tools, update metadata, and draft the next edition
- **Output**: Commits to the repo with the updated roster and new edition

### GitHub Actions (optional)

For automatic metadata refresh (GitHub stars, last push dates, latest releases), a GitHub Actions workflow can be configured:

```yaml
name: Monthly Metadata Refresh
on:
  schedule:
    - cron: '0 7 1 * *'
  workflow_dispatch:
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Refresh metadata
        run: python scripts/refresh_metadata.py
      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git commit -m "Monthly metadata refresh: $(date +%Y-%m)" || echo "No changes"
          git push
```

## License

Content: CC BY 4.0  
Code: MIT
