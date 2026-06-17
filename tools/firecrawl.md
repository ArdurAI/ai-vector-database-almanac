# Firecrawl

An API-first web scraping and document parsing service. Rust-based PDF engine, MCP server, and the cleanest path from URL to RAG-ready Markdown.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 88/100 | JavaScript rendering, anti-bot handling, clean markdown extraction. ~96% web coverage. Structured extraction via LLM |
| **Speed** | 85/100 | p95 latency ~3.4s across millions of pages. JS rendering adds 2-5× latency. Batch processing available |
| **Token Economics** | 80/100 | Free: 500 credits/mo. Hobby: $16/mo (3K credits). Standard: $83/mo (100K credits). 1 credit ≈ 1 page scrape |
| **Scale** | 82/100 | Batch async scraping. Crawl entire sites. 200M+ pages/week processed on managed platform. Rate limits apply |
| **Ops Burden** | 90/100 | Zero infrastructure. API-first. MCP server for agent integration. No parser to self-host |
| **Developer Experience** | 90/100 | Excellent API and SDK. Clean markdown output. Firecrawl MCP server. Playground. Good docs |
| **Data Sovereignty** | 60/100 | Cloud API only. No self-host option. AGPL for self-hosted forks. Data passes through Firecrawl servers |
| **Composite** | **82/100** | Best for web→RAG pipelines. Choose when your source is the web, not local files |

## Architecture & Deployment

Firecrawl is a managed API service with a Rust-based scraping engine. It handles the hard parts of web scraping: JavaScript rendering, proxy rotation, anti-bot bypass, rate limiting, and markdown extraction.

**Core capabilities** (via MCP or API):
- `scrape`: Single-URL scraping → markdown. JS rendering optional. 1-5 credits.
- `crawl`: Multi-page site crawling with configurable depth. 1-5 credits per page.
- `search`: Query → search engine → scrape top results. Research agent workflows.
- `extract`: Structured data extraction via LLM with defined schema. 3-10 credits.
- `map`: Discover all URLs on a website instantly.
- `batch_scrape`: Async scraping of thousands of URLs.

**Deployment options**:
- **Firecrawl API (managed)**: Cloud API. Usage-based credits. No infrastructure.
- **Firecrawl MCP Server**: Model Context Protocol server for Claude, Cursor, VS Code. `npm install -g @mendable/firecrawl-mcp`.
- **Self-hosted (AGPL)**: Open-source core under AGPL. Docker container available. Forking requires license compliance.

## Key Features

- **JavaScript rendering**: Handles SPAs, React, Vue, Angular. 96% web coverage claim. `renderJs: true` for JS-heavy pages.
- **Anti-bot handling**: Rotating proxies, orchestration, rate limits, CAPTCHA bypass. No proxy configuration needed.
- **LLM-ready output**: Clean markdown, structured JSON, screenshots. Removes navigation, ads, boilerplate.
- **Actions system**: Click, scroll, type, wait before extracting. For login-required or dynamic content.
- **Media parsing**: PDF, DOCX, audio extraction from URLs.
- **Firecrawl MCP Server**: Exposes `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_search`, `firecrawl_extract` as MCP tools. Any MCP-compatible agent can use it.

## Pricing (April 2026)

| Plan | Monthly | Credits | Notes |
|------|---------|---------|-------|
| Free | $0 | 500 | ~200-500 page scrapes. No card. |
| Hobby | $16 | 3,000 | Individual developers |
| Standard | $83 | 100,000 | Small teams |
| Growth | $333 | 500,000 | Production workloads |
| Enterprise | Custom | Custom | SLA, dedicated support |

**Credit consumption**:
- `scrape` (no JS): 1 credit
- `scrape` (JS render): 2-5 credits
- `crawl` per page: 1-5 credits
- `extract` (LLM): 3-10 credits
- Enhanced proxy: +4 credits when used

## When to Use / When to Avoid

**Use Firecrawl when**:
- Your RAG source is the web (documentation, blogs, product pages, competitor sites)
- You need JavaScript rendering for SPAs
- You want an MCP server that any agent can use for web research
- You need structured extraction from arbitrary web pages
- You want to avoid building and maintaining a scraping infrastructure

**Avoid Firecrawl when**:
- Your documents are local files (PDFs, DOCX) — use Docling, Marker, or LlamaParse instead
- You need air-gapped / on-premise processing (no self-host option for managed API)
- You need to scrape sites that aggressively block all scrapers (use Bright Data or Browserbase)
- Your volume is >1M pages/month and cost matters (self-hosted Crawlee or Playwright may be cheaper)
- You need raw HTML rather than clean markdown (use ScrapingBee or direct HTTP)

## RAG Pipeline Fit

Firecrawl sits at the **ingestion layer** of the RAG pipeline:

```
URL → Firecrawl scrape/crawl → Markdown → Chunking → Embedding → Vector DB
```

It is not a replacement for the vector database or the embedding model. It replaces the custom scraper that most teams build and maintain. For teams already using Firecrawl for web data, adding document parsing is a natural extension.

## License

API: Proprietary. Self-hosted core: AGPL-3.0.

## Roster Status

**Tier A** — Best web-to-RAG parser. Retained in Tier A due to unmatched web coverage and MCP integration. Watch: pricing at scale, self-host option maturity, enterprise feature expansion.
