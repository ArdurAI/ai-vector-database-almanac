# Docling (IBM)

An open-source document parser from IBM Research that converts PDFs, DOCX, images, and more into clean, structured Markdown with layout-aware extraction. The fastest-growing document processing project in open source.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 90/100 | Layout-aware extraction. TableFormer 93.6% table accuracy. Heading hierarchy preserved. Granite-Docling VLM for vision-based understanding |
| **Speed** | 70/100 | CPU mode: slow on large PDFs. GPU mode: fast but requires setup. ~9-10s per complex PDF on CPU |
| **Token Economics** | 98/100 | Free (MIT). Zero per-page cost. Runs entirely locally. No cloud dependency |
| **Scale** | 75/100 | Single-node, file-based. Batch processing via CLI or API. No distributed processing |
| **Ops Burden** | 80/100 | `pip install docling`. Download models (~2-5GB). Python 3.10+. GPU optional |
| **Developer Experience** | 85/100 | Good Python API. DoclingDocument structured output. LangChain/LlamaIndex/CrewAI integrations. MCP server |
| **Data Sovereignty** | 98/100 | Fully local. Zero cloud calls. MIT license. Runs air-gapped. Critical for regulated docs |
| **Composite** | **85/100** | Best free open-source layout parser. Choose when you need local, high-quality PDF parsing with structure preservation |

## Architecture & Deployment

Docling is built by IBM Research Zurich. It uses a pipeline of models for layout detection, table extraction, reading order analysis, and OCR (via RapidOCR). The January 2026 Granite-Docling release merges a Granite 3 language backbone with a SigLIP2 visual encoder for end-to-end vision+language document understanding.

**Key architectural features**:
- **DoclingDocument format**: Structured JSON output preserving heading hierarchy, table structure, code blocks, mathematical formulas, and reading order. Not just text — the structure of the document.
- **TableFormer**: Proprietary table extraction model. Claims 93.6% accuracy vs. Tabula 67.9% and Camelot 73.0%.
- **Granite-Docling VLM**: Vision-language model for understanding rendered pages as a human would. Replaces the cascade of OCR → layout → post-processing with a single model.
- **RapidOCR**: Built-in OCR for scanned documents. Supports 84+ languages.
- **Heron layout model**: Layout detection for multi-column, complex documents.

**Deployment options**:
- **Python library**: `pip install docling`. Local execution. Models downloaded on first run.
- **Docling MCP Server**: `npx -y docling` or `docling-serve` for FastAPI serving. MCP integration for Claude/Cursor.
- **Container**: `docling-serve` Docker image for API serving.
- **Linux Foundation**: Graduated to LF AI & Data Foundation. Strong governance.

## Key Features

- **Multi-format**: PDF, DOCX, PPTX, XLSX, HTML, images, audio (WAV/MP3), LaTeX, plain text, USPTO patents, XBRL financial reports.
- **Structured output**: DoclingDocument JSON with semantic hierarchy (title, heading, paragraph, table, figure, code, formula).
- **Layout preservation**: Multi-column layout, reading order, page breaks, footnotes.
- **MCP integration**: Built-in MCP server. Agents can parse documents natively.
- **LangChain/LlamaIndex**: Native loaders (`DoclingLoader`, `DoclingReader`).
- **Milvus integration**: Built-in upload to Milvus for RAG workflows.
- **Table accuracy**: 93.6% TEDS (Table Extraction Detection Score) on benchmarks.

## Benchmarking

### Accuracy Claims (2026)

| Metric | Docling Claim | Independent Result | Verdict |
|--------|--------------|-------------------|---------|
| TableFormer accuracy | 93.6% | Not independently verified | ⚠️ Pending |
| TEDS score | 0.911 (v1.5.1) | ~0.877 on opendataloader-bench | ✅ Close |
| Overall opendataloader | 0.877 | ~0.877-0.905 (pdfmux claims 0.905) | ✅ Close |
| Markdown fidelity | High | Good on structured docs, mixed on scanned | ✅ Plausible |

### Performance

| Mode | Speed | Notes |
|------|-------|-------|
| CPU (standard) | ~9-10s per complex PDF | Sufficient for batch processing |
| GPU (Granite-Docling) | ~2-3s per page | Requires CUDA setup |
| FastAPI serve | API latency ~200ms | Containerized deployment |

## When to Use / When to Avoid

**Use Docling when**:
- You need 100% local processing (air-gapped, regulated, sensitive documents)
- You need structured output with heading hierarchy and table fidelity
- You are building a RAG pipeline with LlamaIndex or LangChain
- You want a free, open-source alternative to commercial parsers
- Your documents are technical reports, manuals, financial statements, or academic papers
- You need MCP server integration for agent workflows

**Avoid Docling when**:
- You need the fastest possible parsing (Marker or PyMuPDF4LLM are faster on simple PDFs)
- You need handwriting or form-field extraction (use LandingAI ADE or Reducto)
- You are on Node.js or Java (Python-only ecosystem)
- You need a fully managed SaaS with SLAs (use LlamaParse or Reducto)
- You need the absolute highest table accuracy on complex nested tables (Reducto claims ~20% higher)

## RAG Pipeline Fit

```
PDF/DOCX → Docling parse → DoclingDocument JSON → Chunking (by-title, by-section) → Embedding → Vector DB
```

Docling's `by-title` chunking strategy leverages detected document structure to preserve section boundaries. This is a genuine advantage over simple sliding-window chunking that breaks semantic coherence.

## License

MIT (open-source). No usage limits, no pricing tiers, no vendor lock-in.

## Roster Status

**Tier A** — Best free open-source layout parser. Retained in Tier A due to unmatched structure fidelity, local execution, and rapid ecosystem growth (61K+ stars). Watch: Granite-Docling GPU adoption, multi-language expansion, table accuracy on real-world benchmarks.
