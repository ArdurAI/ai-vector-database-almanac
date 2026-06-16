# Troubleshooting & Debugging

How to understand the codebase, debug issues, and resolve common problems when working with the vector database almanac.

## Table of Contents

1. [Understanding the Codebase](#understanding-the-codebase)
2. [Common Issues](#common-issues)
3. [Debugging the Data Pipeline](#debugging-the-data-pipeline)
4. [Debugging Benchmark Runs](#debugging-benchmark-runs)
5. [FAQ](#faq)
6. [Getting Help](#getting-help)

---

## Understanding the Codebase

### High-level flow

```
Research Agents → Research Output (Markdown) →
  Python Script → roster.json (Structured Data) →
    Manual Review → Edition Markdown →
      Git Commit → GitHub Publication
```

### Key files and their roles

| File | Role | When to read it |
|------|------|-----------------|
| `README.md` | Project overview, quick reference | First thing you read |
| `INTENT.md` | Philosophy, why we do things this way | When you disagree with a decision |
| `IMPLEMENTATION.md` | How things are built, how to add tools | When you want to contribute |
| `TESTING.md` | Benchmark methodology, scoring, adapter contract | When you want to reproduce or challenge a result |
| `TROUBLESHOOTING.md` | This file | When something is broken |
| `architecture.md` | Stack architecture diagram | When you want to understand the big picture |
| `editions/YYYY-MM.md` | Monthly snapshot of the landscape | When you want historical data |
| `data/roster.json` | Machine-readable catalog | When you want to query or analyze the data |
| `methodology/benchmark-harness.md` | Harness specification | When you want to build an adapter or run benchmarks |
| `benchmarks/<suite>/<tool>-<dataset>-<date>.json` | Raw results | When you want to re-analyze or challenge a score |

### The data model

The almanac is fundamentally a **directed graph** of data:

```
Research findings → Tool metadata → Roster JSON → Edition Markdown → README
                                      ↓
                               Benchmark results → Per-tool pages
```

- **Research findings** are the raw output of the research swarm. They're saved in `research/` (not in the public repo).
- **Tool metadata** is extracted from research and stored in `data/roster.json`.
- **Roster JSON** is the single source of truth. Everything else derives from it.
- **Edition markdown** is human-written based on the roster and research.
- **README** is auto-generated from the roster and the latest edition.

### Understanding `data/roster.json`

This is the most important file in the repo. It is the single source of truth.

**Structure**:
```json
{
  "meta": { ... },
  "categories": {
    "vector-databases": {
      "name": "Vector Databases & ANN Libraries",
      "description": "...",
      "estimated_total": N,
      "tools": [
        { "name": "...", "type": "...", "license": "...", "tier": "A|B|C", "notes": "..." }
      ]
    }
  }
}
```

**How to query it**:
```bash
# Find all Tier A vector databases
jq '.categories."vector-databases".tools[] | select(.tier == "A") | .name' data/roster.json

# Count tools by tier
jq '.categories | to_entries[] | .value.tools | group_by(.tier) | map({tier: .[0].tier, count: length})' data/roster.json

# Find all MIT-licensed tools
jq '.. | objects | select(.license == "MIT") | .name' data/roster.json

# Find all managed services
jq '.categories."vector-databases".tools[] | select(.type == "Managed Service") | .name' data/roster.json
```

### The edition markdown

Editions are **human-written** summaries, not machine-generated. They are based on the roster but include analysis, interpretation, and narrative that a machine can't produce.

**How editions are structured**:
1. Front matter: date, research method, context
2. Landscape at a glance: summary table with recall/latency metrics
3. Per-tool sections: findings, roster, analysis, cost tracking
4. Quest diary: what was tested this month (which benchmarks, which tools)
5. Stress suite findings: patterns that span tools

### The benchmark harness (separate repo)

The actual benchmark code lives in a separate repository. The almanac repo contains:
- The methodology specification
- The results (JSON + markdown)
- The adapter interface definitions

The harness repo contains:
- The runner code
- The VectorDBAdapter implementations
- The telemetry collector (recall, latency, memory)
- The grading pipeline (exact recall, BEIR NDCG)

**Why separate?** Because the harness is code that runs, and the almanac is data that is published. They have different lifecycles and different audiences.

## Common Issues

### Issue: `roster.json` is invalid JSON

**Symptoms**:
- `jq` fails to parse it
- GitHub Actions fails on JSON validation
- Python `json.load()` raises `JSONDecodeError`

**Diagnosis**:
```bash
python3 -c "import json; json.load(open('data/roster.json'))"
```

**Resolution**:
1. Find the line with the error: `python3 -m json.tool data/roster.json`
2. Common causes: trailing commas, unescaped quotes, incorrect nesting, tool names with special characters
3. Fix the JSON and re-validate
4. Consider using a JSON linter in your editor

### Issue: Edition markdown has broken links

**Symptoms**:
- Links to tools return 404
- Links to benchmarks don't exist yet
- Relative links work locally but break on GitHub

**Diagnosis**:
```bash
# Check all links in the repo
find . -name "*.md" -exec grep -oP '\[.*?\]\(.*?\)' {} + | grep -v "http" | grep -v "mailto"
```

**Resolution**:
1. For internal links, use relative paths: `../data/roster.json`
2. For external links, verify the URL is correct (vendor docs move frequently)
3. For tools without a per-tool page yet, link to their homepage or GitHub repo
4. Run a link checker as part of CI

### Issue: Tier assignment is wrong

**Symptoms**:
- A tool is Tier A but has no production usage at scale (e.g., no 1M+ vector deployments)
- A tool is Tier C but is widely adopted (e.g., pgvector in thousands of Postgres deployments)
- A tool's tier changed without explanation

**Diagnosis**:
1. Check the tier assignment rules in `IMPLEMENTATION.md`
2. Verify the tool's adoption, activity, and community health (GitHub issues, Discord, HN mentions)
3. Check the edition notes for the rationale
4. Check benchmark results: does it have competitive recall@100 and latency?

**Resolution**:
1. File an issue with evidence (GitHub stars, last push, production references, benchmark numbers)
2. The tier will be reviewed in the next edition cycle
3. Tiers are not changed mid-edition; they are updated at edition boundaries

### Issue: Benchmark results can't be reproduced

**Symptoms**:
- Running the harness produces different recall@k numbers
- The adapter fails with a different tool version
- The embedding model is unavailable or produces different vectors
- Results differ by >5% on the same hardware

**Diagnosis**:
1. Check the `results.json` metadata for the exact commit, seed, hardware, embedding model, and tool version
2. Check if the tool version has changed since the published run (index algorithms change)
3. Verify the embedding model is the exact pinned version (model updates change vector outputs)
4. Check if the distance metric was correctly configured (cosine vs. dot-product vs. Euclidean)
5. Check if `ef` or `nprobe` parameters match the published configuration

**Resolution**:
1. Use the exact commit, dependencies, and model from the results metadata
2. If the tool version changed, the results are for a different version — this is expected
3. If the embedding model changed, that's a methodology issue — file an issue
4. If the adapter used different index parameters, check the adapter implementation

### Issue: Adapter fails on embedding model mismatch

**Symptoms**:
- Adapter crashes with "dimension mismatch" or "expected 384, got 768"
- Query returns empty results because the embedding model changed between ingest and query
- Results are nonsense because the model produces different vectors for the same text

**Diagnosis**:
1. Check the adapter's `setup()` — what dimension is it using?
2. Check the embedding model version in the harness config vs. the adapter
3. Check if the tool has a built-in embedding model that conflicts with the harness model

**Resolution**:
1. The adapter must use the harness's frozen embedding model, or document why it uses a different one
2. If the tool requires its own model (e.g., for hybrid search), the adapter must bridge the two models correctly
3. Document the model mismatch in the results metadata and the per-tool page

### Issue: Benchmark results inconsistent due to index parameters

**Symptoms**:
- Same tool, same dataset, different recall@100 across runs
- Latency varies by 2x with no hardware change
- One run shows 95% recall, another shows 85% recall on the same tool

**Diagnosis**:
1. Check if the tool auto-tunes index parameters differently per run (e.g., based on available RAM)
2. Check if `ef` or `nprobe` was set differently (maybe the adapter has a bug)
3. Check if the index was fully built before querying (`await_ready()` may have returned early)
4. Check if the tool uses random initialization (some graph-based ANN methods do)
5. Check if concurrent queries affected build quality

**Resolution**:
1. Pin all index parameters in the adapter and log them
2. Set `ef` or `nprobe` explicitly, don't rely on defaults
3. Ensure `await_ready()` waits for the actual index state (not just the API response)
4. Run multiple seeds and report confidence intervals
5. Document auto-tuning behavior in the per-tool page

### Issue: Distance metric differences

**Symptoms**:
- Tool A and Tool B produce different top-k for the same query vector on the same dataset
- A tool claiming "cosine" produces different results than brute-force cosine
- Normalization issues: some tools normalize internally, others don't

**Diagnosis**:
1. Verify the tool's actual distance implementation (check source code if open source)
2. Check if the tool normalizes vectors on insert (e.g., for cosine, some tools store normalized vectors)
3. Check if the adapter is passing the metric correctly (string vs. enum vs. API parameter)
4. Compute brute-force cosine/Euclidean/dot-product yourself and compare

**Resolution**:
1. Document the exact distance metric behavior in the adapter comments
2. If the tool has a known quirk (e.g., "cosine" actually means "normalized dot-product"), document it
3. For fair comparison, ensure all tools use the same metric semantics or document the difference
4. Add a "distance metric torture" test to the stress suite to catch this

### Issue: Research agent missed a tool

**Symptoms**:
- A well-known vector DB is not in the roster (e.g., a new ANN library from a major conference)
- A tool from a specific region is missing (e.g., Chinese vector databases)
- A newly launched managed service is not in the latest edition

**Diagnosis**:
1. Check if the tool meets triage criteria in `IMPLEMENTATION.md`
2. Check if it was added in a previous edition and later removed (dead/abandoned)
3. Check if it falls outside the search scope (e.g., it's a full-text engine with no vector support)

**Resolution**:
1. File an issue with the tool name, URL, and evidence of adoption/activity
2. The tool will be triaged for the next edition
3. If it meets criteria, it will be added

### Issue: Monthly update cron failed

**Symptoms**:
- No new edition was published on the 15th
- The cron job is missing from the scheduler
- The research agent timed out

**Diagnosis**:
```bash
# Check cron status
cron status

# Check the cron job list
# (use the Kimi Work cron interface)
```

**Resolution**:
1. Check if the cron job is still registered
2. Check if the research agent timed out (increase timeout if needed; vector DB research is complex)
3. Manually trigger the update if the cron missed a cycle
4. Check the workspace path in the cron job configuration

### Issue: GitHub push fails

**Symptoms**:
- `git push` returns 403 or 401
- The remote is not configured
- The branch is behind origin

**Diagnosis**:
```bash
git remote -v
git status
git log --oneline -5
```

**Resolution**:
1. Verify the remote URL is correct: `git remote set-url origin https://github.com/ArdurAI/...`
2. Verify GitHub CLI auth: `gh auth status`
3. If behind origin, pull first: `git pull origin main`
4. If there are conflicts, resolve them manually

## Debugging the Data Pipeline

### Research output → roster.json

**Problem**: Research agents produce markdown, but the roster JSON is incomplete or wrong.

**Debug steps**:
1. Read the research output files in `research/` (local workspace, not in the repo)
2. Check if the Python extraction script correctly parsed the tool tables
3. Check if tools were dropped during triage (check the triage log)
4. Verify the JSON schema is correct
5. Check for vector DB-specific fields: does the tool have `index_types`, `distance_metrics`, `hybrid_search` fields if applicable?

**Common bugs**:
- Tool names with special characters break JSON parsing → Escape them properly
- Tools with no tier get dropped → Default to Tier C if unsure
- Tools with no notes get empty strings → Add a minimal note about index types
- Tools with type "Vector DB" vs. "ANN Library" vs. "Managed Service" get mixed up → Check the type definitions

### roster.json → edition markdown

**Problem**: The edition doesn't reflect the roster.

**Debug steps**:
1. Compare the tool counts in the roster vs. the edition
2. Check if the edition was written before the roster was updated
3. Check if tools were manually edited in the edition but not in the roster

**Resolution**:
1. The edition should be derived from the roster, not the other way around
2. If the edition has manual additions, ensure they are also in the roster
3. The edition is a human-readable summary; the roster is the source of truth

### Edition markdown → README

**Problem**: The README roster-at-a-glance doesn't match the latest edition.

**Debug steps**:
1. Check which edition is referenced in the README
2. Check if the README was updated after the edition was published
3. Check if the README lists the correct Tier A count and names

**Resolution**:
1. The README should always reference the latest edition
2. Update the README when a new edition is published
3. Consider automating README updates from the roster JSON

## Debugging Benchmark Runs

### The adapter fails

**Symptoms**:
- `setup()` crashes (Docker not available, port conflict)
- `load()` throws an exception (dimension mismatch, batch size too large)
- `search()` returns nothing or garbage (index not built, wrong metric, empty collection)
- `build_index()` hangs or crashes (OOM, unsupported index type)

**Debug steps**:
1. Run the adapter in isolation (without the harness)
2. Check the tool's documentation for setup requirements (e.g., `vm.max_map_count`, CUDA drivers)
3. Check if environment variables are set (API keys for managed services)
4. Check if the tool version matches what the adapter expects
5. Check if the embedding model dimension matches the collection dimension

**Common fixes**:
- Missing Docker daemon → Start Docker
- Missing API key → Set the environment variable (e.g., `PINECONE_API_KEY`)
- Wrong tool version → Update the adapter or pin the version
- Dependency conflict → Use a virtual environment or container
- Dimension mismatch → Verify the adapter uses the harness's dimension (384 or 768)
- Index parameter error → Check if the tool supports the requested index type (HNSW, IVF, etc.)

### The canary fails

**Symptoms**:
- The no-DB baseline scores above zero on recall@k
- The canary returns non-empty results
- The canary crashes during the search phase

**Debug steps**:
1. Check if the benchmark workload has leaked ground-truth vectors into the query set
2. Check if the grading pipeline has a bug (computing recall against the wrong ground truth)
3. Check if the random seed was set (shouldn't matter for canary, but good to check)
4. Check if the canary adapter is truly a no-op (does it accidentally share state with real adapters?)

**Resolution**:
1. If the workload leaked answers, redesign the workload (ensure query vectors are not in the index)
2. If the grader has a bug, fix the grader and rerun all tests
3. This is a critical failure — the entire batch is invalid

### Results are inconsistent

**Symptoms**:
- Same tool, same test, different recall@k across runs
- Latency varies by more than the confidence interval
- Memory usage differs by 2x between runs

**Debug steps**:
1. Check if the tool has non-deterministic behavior (e.g., HNSW graph construction with random seeds)
2. Check if the hardware was different between runs (different CPU, RAM pressure)
3. Check if the tool version changed between runs
4. Check if index auto-tuning chose different parameters based on system load
5. Check if `await_ready()` timing differs (background indexing may finish at different times)

**Resolution**:
1. Pin the tool's random seed if it exposes one (e.g., FAISS `seed` parameter)
2. Record hardware specs and system load in the results metadata
3. Pin tool versions and record them
4. Run warm-up queries before measurement to stabilize the index
5. Increase the number of runs and report confidence intervals

## FAQ

### Q: Why is tool X not in the roster?

A: Either it doesn't meet triage criteria, it hasn't been discovered yet, or it was removed for inactivity. File an issue with evidence and we'll triage it. For vector DBs, we also check: does it support at least 100K vectors? Does it support standard distance metrics?

### Q: Why did tool X's recall score change?

A: Either the tool was updated (new index algorithm, default parameter change), the methodology was refined (new embedding model, new dataset), or we found a bug in our previous adapter (wrong `ef` value, wrong distance metric). All three are valid reasons. Check the edition notes for the rationale.

### Q: Can I run the benchmarks myself?

A: Yes. The harness is published separately. Clone it, install dependencies (including the pinned embedding model), download the datasets, and run the adapter for the tool you want to test. See `TESTING.md` for reproducibility instructions. Note: you need enough RAM for the dataset (e.g., 1M vectors × 384 dims × 4 bytes ≈ 1.5GB minimum, plus index overhead).

### Q: How do I challenge a ranking?

A: File an issue with specific evidence. Check the raw results JSON (every query vector, every returned neighbor), the adapter code (did it use the right `ef`? The right distance metric?), and the benchmark parameters. If you find a real problem, we'll re-run or update the methodology.

### Q: Can I add a tool to the roster?

A: Yes. See `CONTRIBUTING.md` for instructions. The tool must meet triage criteria and pass the smoke gate (create collection, insert 1K vectors, query with recall@10 > 0.8).

### Q: Why are there separate category almanacs?

A: Each category is deep enough to warrant its own dedicated repo with per-tool pages, category-specific benchmarks, and focused community. The parent almanac is the master catalog. Vector databases have unique concerns (ANN accuracy, index tuning, embedding costs) that deserve deep treatment.

### Q: How often are benchmarks re-run?

A: Standard (ANN-Benchmarks, BEIR, MS MARCO): every quarter for each tool. Stress suite: annually. Integration tests (RAG stack): quarterly. If a tool releases a major version (e.g., Milvus 3.0, Qdrant 2.0), we may re-run early.

### Q: What's the difference between Tier A, B, and C?

A: Tier A = market leader or strongest recall/latency tradeoff with production usage at scale. Tier B = solid option, specific use cases (embedded, multi-modal, specific cloud). Tier C = niche, early-stage, or specialized. See `IMPLEMENTATION.md` for full rules.

### Q: Why does the same tool have different scores on different datasets?

A: Because different datasets stress different aspects of a vector DB. SIFT1M tests pure ANN speed; BEIR tests retrieval quality with real text; MS MARCO tests scale and metadata filtering. A tool that is great on SIFT may struggle with BEIR if its hybrid search is weak. We publish all scores so you can choose based on your workload.

### Q: Can vendors sponsor the almanac?

A: No. The almanac is independently funded. Sponsorship would compromise the core mission. Vendors can improve their scores by actually improving their tools (better recall, lower latency, easier ops).

### Q: My tool uses a custom index type not in the standard benchmarks. How do I get it tested?

A: File an issue with the tool details and the custom index type. We'll evaluate if the index type is significant enough to add a custom benchmark or adapter variant. If it's a novel algorithm (e.g., a new graph-based method), we may add it to the ANN-Benchmarks suite.

## Getting Help

### File an issue

GitHub issues are the primary support channel. Use the appropriate template:

- **Tool request**: "Add [Tool Name] to Vector Databases"
- **Data correction**: "[Tool Name] metadata is wrong: [what's wrong]"
- **Benchmark challenge**: "Challenge [Tool Name] ranking on [Dimension]: [evidence]"
- **Adapter bug**: "[Tool Name] adapter fails on [scenario]: [traceback]"
- **Bug report**: "[Bug description] in [file/process]"
- **Feature request**: "[Feature description] for [use case]"

### Discussion

GitHub Discussions are for:
- General questions about the almanac
- Sharing experiences with vector DBs on the roster (e.g., "We run Milvus at 50M vectors — here's what we learned")
- Proposing methodology changes (e.g., "Should we add a GPU benchmark?")
- Community announcements (e.g., "I built an adapter for [new tool]")
- Index tuning tips and tricks

### Email

For private or sensitive inquiries: Use the contact info in the ArdurAI org profile.

## License

Content: CC BY 4.0
