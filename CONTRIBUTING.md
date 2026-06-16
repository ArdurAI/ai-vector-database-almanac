# Contributing to the Vector Databases Almanac

How to add tools, fix data, challenge rankings, and improve the methodology for vector databases and retrieval systems.

## Table of Contents

1. [Ways to Contribute](#ways-to-contribute)
2. [Adding a New Vector Database](#adding-a-new-vector-database)
3. [Fixing Data](#fixing-data)
4. [Challenging a Ranking](#challenging-a-ranking)
5. [Improving the Methodology](#improving-the-methodology)
6. [Code of Conduct](#code-of-conduct)
7. [License](#license)

---

## Ways to Contribute

You can contribute to the almanac in several ways:

| Contribution Type | What you do | Impact |
|-------------------|-------------|--------|
| **Add a tool** | File an issue with a new vector database or ANN library | Expands the roster |
| **Fix data** | Correct incorrect metadata (license, tier, index types) | Improves accuracy |
| **Challenge a ranking** | Provide evidence that a recall or latency score is wrong | Drives quality |
| **Share experience** | Write about using a vector DB in production at scale | Adds real-world context |
| **Improve methodology** | Propose a better benchmark, dataset, or scoring rubric | Improves fairness |
| **Build an adapter** | Implement the VectorDBAdapter for a new tool | Enables testing |
| **Review an edition** | Proofread, fact-check, suggest improvements | Improves quality |
| **Spread the word** | Share the almanac with your community | Grows the ecosystem |
| **Add a hybrid search test** | Contribute a new stress suite for sparse+dense retrieval | Improves coverage |

## Adding a New Vector Database

### Before you submit

Check if the tool meets the triage criteria:

1. **Seriousness**: Is it a real tool with real users, not a toy or demo? Must handle 100K+ vectors or have a clear path to it.
2. **Activity**: Has it had a push or release in the last 6 months?
3. **Documentation**: Does it have a README, docs, or landing page explaining indexing, querying, and distance metrics?
4. **Accessibility**: Is it testable (open source, free tier, or evaluation license)? Must support standard metrics (cosine, Euclidean, dot-product).
5. **Scope**: Does it fit the vector database category? A general-purpose DB with a vector extension qualifies; a pure full-text engine without vector support does not.

### How to submit

**Option 1: GitHub Issue (preferred)**

File an issue with this template:

```markdown
## Tool Request: [Tool Name]

### Category
Vector Databases & ANN Libraries

### Tool URL
[GitHub repo or homepage URL]

### License
[e.g., MIT, Apache-2.0, Proprietary]

### Type
[Vector DB | ANN Library | Managed Service | Database Extension]

### Description
[What does it do? One paragraph. Mention supported index types (HNSW, IVF, etc.) and distance metrics.]

### Why it should be on the roster
[Evidence of adoption, production usage at scale, or technical merit (novel algorithm, competitive ANN-Benchmarks numbers).]

### Evidence
- GitHub stars: [N]
- Last release: [date]
- Notable users: [companies, if known]
- Funding: [amount, if known]
- ANN-Benchmarks entry: [link, if available]
- Supported index types: [HNSW, IVF, PQ, etc.]
- Supported distance metrics: [cosine, Euclidean, dot-product, etc.]
- Metadata filtering: [yes/no, and how (key-value, JSON, SQL-like)]
- Hybrid search: [yes/no, and how (sparse+dense, BM25+vectors, reranking)]

### Tier suggestion
[A, B, or C — and why]

### Can you help build the adapter?
[yes/no — if yes, mention your experience with the tool's SDK/API]
```

**Option 2: Pull Request**

If you want to add the tool directly:

1. Fork the repo
2. Edit `data/roster.json` to add the tool to the `vector-databases` category
3. Update `editions/YYYY-MM.md` if the tool is Tier A
4. Update `README.md` if the tool is Tier A
5. If you have benchmark results, add them to `benchmarks/<suite>/`
6. Submit a PR with the same template as above

### What happens after submission

1. **Triage**: We check if the tool meets criteria (within 7 days)
2. **Smoke gate**: We run the tool through the 3-turn scenario (create collection, insert 1K vectors, query with recall@10 > 0.8) (within 14 days)
3. **Adapter review**: If you submitted an adapter, we review it for correctness and purity
4. **Decision**: Accepted, rejected, or deferred with a note
5. **Publication**: If accepted, it appears in the next edition

## Fixing Data

### If you find incorrect metadata

File an issue with:

```markdown
## Data Correction: [Tool Name]

### Current (incorrect) data
[What does the roster say?]

### Correct data
[What should it say?]

### Evidence
[Link to the source that proves the correct data.]
```

### Common corrections for vector databases

| Field | Common errors | How to verify |
|-------|--------------|---------------|
| License | Wrong SPDX identifier | Check the repo's LICENSE file |
| Stars | Out of date | Check the GitHub API |
| Last push | Wrong date | Check the GitHub repo commits |
| Tier | Wrong tier | Check the tier rules in IMPLEMENTATION.md; check benchmark results |
| Notes | Outdated description | Check the tool's homepage/docs |
| Type | Wrong type | Is it a "Managed Service" or "Vector DB" or "ANN Library"? |
| Index types | Missing or wrong | Check the tool's documentation for supported index types (HNSW, IVF, etc.) |
| Distance metrics | Missing or wrong | Check the tool's documentation for supported metrics (cosine, Euclidean, dot-product) |
| Hybrid search | Outdated | Check the tool's latest release notes for hybrid search support |
| Cost | Outdated | Check the vendor's pricing page for managed services |

### What happens after submission

Data corrections are reviewed and applied in the next edition cycle. We don't edit editions retroactively; we correct the data and note it in the next edition.

## Challenging a Ranking

### If you believe a score is wrong

File an issue with:

```markdown
## Challenge: [Tool Name] on [Dimension]

### Current score
[What does the almanac say?]

### Your evidence
[What data do you have?]

### What you did to verify
[Steps you took to reproduce or verify.]

### Suggested resolution
[What should change? Re-run? Different score? Methodology update?]
```

### What evidence is valid

| Evidence Type | Strength | Example |
|---------------|----------|---------|
| Raw results JSON analysis | Strong | "I re-analyzed the JSON and found that recall@100 was computed against the wrong ground truth for Tool X" |
| Independent reproduction | Strong | "I ran the harness with the same adapter and got 87% recall@100, not 95%" |
| Adapter bug documentation | Strong | "The adapter uses `ef=64` but the tool's documentation says `ef=128` is required for this dataset size" |
| Distance metric mismatch | Strong | "The adapter configured 'cosine' but the tool actually uses normalized dot-product, causing a silent recall drop" |
| Index parameter issue | Medium | "The tool auto-tuned to `m=8` but the vendor recommends `m=16` for 1M vectors" |
| Vendor claim | Weak | "The vendor says Z" — but we already test vendor claims independently |
| Anecdote | Weak | "It worked for me" — not reproducible |

### What happens after submission

1. **Review**: We review the evidence (within 7 days)
2. **Reproduction**: If the claim is reproducible, we re-run the test with the corrected adapter or parameters
3. **Update**: If the re-run confirms the challenge, we update the score
4. **Publication**: The update appears in the next edition with a note about the challenge

### Special considerations for vector databases

- **Embedding model mismatch**: If the challenge is about the embedding model used, we check if the model was pinned correctly and if the adapter used the same model for ingest and query.
- **Index parameters**: If the challenge is about `ef`, `nprobe`, `m`, or `efConstruction`, we verify the adapter set these explicitly and logged them. Auto-tuning must be documented.
- **Dataset specifics**: If the challenge is about a specific dataset (e.g., "Tool X should perform better on GloVe-200"), we check if the dataset was loaded correctly and the dimension matches.
- **Hardware differences**: If you ran on different hardware, we note the hardware in the results and may re-run on our standard hardware for comparison.

## Improving the Methodology

### If you want to propose a methodology change

File an issue with:

```markdown
## Methodology Proposal: [Title]

### Current state
[What does the methodology say now?]

### Proposed change
[What should it say?]

### Rationale
[Why is this better? What problem does it solve?]

### Impact
[Which tools would be affected?]

### Backward compatibility
[Can old results be re-scored with the new method?]
```

### Methodology change process

1. **RFC**: The proposal is posted as an RFC for public comment (30 days)
2. **Discussion**: Community feedback is collected
3. **Decision**: ArdurAI makes the final decision based on feedback
4. **Announcement**: If accepted, a public announcement is made with a transition plan
5. **Implementation**: The change is implemented in the next edition cycle
6. **Re-run**: Affected benchmarks are re-run with the new methodology

### What kinds of changes are accepted

| Change Type | Likelihood | Example |
|-------------|------------|---------|
| Bug fix in harness or adapter | High | "The adapter incorrectly handles `ef` parameter for HNSW indices" |
| New benchmark dataset | Medium | "Add the Deep1B 10M subset to ANN-Benchmarks" |
| New benchmark suite | Medium | "Add a sparse retrieval benchmark (e.g., SPLADE) for hybrid search tools" |
| Weight adjustment | Medium | "Increase ops burden weight from 15% to 20% because HNSW tuning is too complex" |
| New dimension | Low | "Add a 'hybrid search quality' dimension" |
| Remove dimension | Very low | "Remove latency as a dimension" |
| Embedding model update | Low | "Update from all-MiniLM-L6-v2 to a newer model" — requires re-running all benchmarks |

### What kinds of changes are rejected

- Changes that favor a specific vendor or tool
- Changes that reduce reproducibility (e.g., removing frozen parameters)
- Changes that increase complexity without clear benefit (e.g., adding 10 new datasets with no clear distinction)
- Changes that are not backward-compatible without a migration plan
- Changes that would require re-running all benchmarks without sufficient justification

### Vector-database-specific methodology improvements we welcome

- **New ANN datasets**: Datasets that stress specific aspects (high dimensionality, sparse vectors, multi-modal embeddings)
- **Hybrid search benchmarks**: Tests for sparse+dense retrieval, BM25+vector fusion, reranking pipelines
- **GPU index benchmarks**: If GPU-based ANN libraries become mainstream, we may add a GPU benchmark track
- **Real-time ingestion benchmarks**: Tests for insert-and-query workloads (streaming vectors, not batch)
- **Metadata filtering benchmarks**: Structured tests for complex filters (range queries, nested JSON, AND/OR logic)
- **Cross-region latency tests**: For managed services, measuring query latency from different geographic regions

## Code of Conduct

### Be respectful

This is a collaborative project. Treat others with respect, even when you disagree. Vector database debates can get heated (HNSW vs. IVF vs. graph-based); keep it civil.

### Be evidence-based

Claims should be backed by evidence. "I think X is better" is not enough. "I measured X and found Y on the ANN-Benchmarks suite" is. If you challenge a ranking, bring numbers.

### Be constructive

Criticism is welcome if it's constructive. "This is wrong" is not helpful. "This is wrong because the adapter used `ef=64` instead of `ef=128`, and here's the benchmark run that proves it" is.

### Be patient

The almanac is maintained by a small team. Responses may take time. Repeated pings are not helpful. Benchmark re-runs take time (especially for large datasets like MS MARCO).

### No spam

Don't submit the same tool multiple times. Don't submit tools that clearly don't meet criteria (e.g., a 50-star repo with no vector operations). Don't use the almanac for marketing. Don't submit affiliate links.

## License

By contributing to the almanac, you agree that your contributions are licensed under CC BY 4.0 for content and MIT for code.

## Attribution

Contributors are recognized in the edition notes. If you make a significant contribution (e.g., adding 5+ tools, fixing major data issues, improving methodology, building adapters), you will be listed as a contributor in the next edition.

## License

Content: CC BY 4.0  
Code: MIT
