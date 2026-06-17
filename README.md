# Vector Databases & RAG Infrastructure Almanac

A living encyclopedia of vector databases, ANN libraries, and RAG infrastructure. Updated monthly with fresh repo metadata, releases, landscape shifts, and independent benchmark results.

> Vendors publish their own benchmark numbers. Nobody reproduces them independently, and nobody evaluates tools the way a platform engineer has to live with them: ops burden, failure modes, scale curves, and cost. This almanac is the public record of that work.

## Current status

**Founding edition (2026-06)**: 80 tools catalogued, 5 Tier A vector database deep-dives published, methodology frozen. No independent benchmark results yet — first benchmark batch scheduled for July 2026.

## How to use this repo

| You want… | Go to |
|-----------|-------|
| The state of the landscape right now | `editions/2026-06.md` |
| Everything we know about one tool | `tools/<name>.md` (see below) |
| Machine-readable roster + metadata | `data/roster.json` |
| Architecture diagrams | `architecture.md` |
| Benchmark results (rolling) | `benchmarks/` |
| How tools are tested and ranked | `methodology/benchmark-harness.md` |
| Project intent & philosophy | `INTENT.md` |
| Implementation guide & how to add tools | `IMPLEMENTATION.md` |
| Testing methodology & benchmarks | `TESTING.md` |
| Troubleshooting & debugging | `TROUBLESHOOTING.md` |
| How to contribute | `CONTRIBUTING.md` |

## Tool deep-dives (published)

| Tool | Tier | File | Notes |
|------|------|------|-------|
| **Pinecone** | A | [`tools/pinecone.md`](tools/pinecone.md) | Managed leader; zero ops; cost cliff at scale |
| **Qdrant** | A | [`tools/qdrant.md`](tools/qdrant.md) | Best self-hosted dedicated; Rust; BQ; $50M Series B |
| **Weaviate** | A | [`tools/weaviate.md`](tools/weaviate.md) | Best hybrid search; MCP server; multimodal |
| **Milvus** | A | [`tools/milvus.md`](tools/milvus.md) | Billion-scale; GPU CAGRA; K8s-native; complex ops |
| **pgvector** | A | [`tools/pgvector.md`](tools/pgvector.md) | Postgres extension; default for <10M vectors; pgvectorscale |

## The roster

**Tier A** — 31 tools: Pinecone, Qdrant, Weaviate, Milvus, Chroma, pgvector, Zilliz / Vector Lakebase, Turbopuffer, Vorkath, LanceDB…

**Tier B** — 46 tools: MongoDB Atlas Vector Search, SingleStore, DataStax Astra (Cassandra), Marqo, ClickHouse, DuckDB, Oracle AI Database 26ai, Apache Cassandra 5.0, Vald, Cloudflare Vectorize…

**Tier C** — 3 tools: pdfmux, MinerU / MinerU-Popo, Vectorize AI

**Total: 80 tools**

## Methodology

Results published here come from a frozen-before-results harness:
- Standard benchmarks for comparability with published claims — every ranking ships a _published vs. reproduced_ table.
- A custom PlatformOps benchmark: testing on infrastructure work — setup, reliability, scale, cost.
- A stress suite: contradiction storms, near-duplicate floods, concurrent writers, kill-the-backing-store chaos, cost-runaway measurement.
- Seven scored dimensions: accuracy, latency, token economics, scale behavior, **ops burden**, developer experience, data sovereignty.

The judge model, prompts (SHA-256-frozen), and control variables were fixed before any tool ran. Raw results JSON is published with every ranking.

## Update cadence

One edition per month under `editions/YYYY-MM.md`: refreshed metadata, notable releases, new entrants triaged in or out, and a diary of what was tested.

## License

Content is licensed CC BY 4.0 — share and adapt with attribution to **ArdurAI / Vector Databases & RAG Infrastructure Almanac**.
