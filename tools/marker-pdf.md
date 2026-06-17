# Marker-PDF

A GPU-accelerated, layout-perfect Markdown converter. The fastest open-source tool for batch PDF→Markdown conversion with image and formula preservation.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 86/100 | Layout-perfect Markdown. Good heading hierarchy. Formula detection. Image extraction. Weaker on very complex multi-page tables |
| **Speed** | 88/100 | ~25 pages/sec on H100 in batch mode. Fast on GPU. CPU mode is viable. The fastest among layout-aware open-source tools |
| **Token Economics** | 95/100 | Free (open-source). Datalab managed platform: $5 free credits. Commercial self-host requires license. Near-zero cost for local use |
| **Scale** | 80/100 | Batch mode on multiple GPUs. CLI, GUI, API, online service. 200M+ pages/week on managed platform. Single-node |
| **Ops Burden** | 85/100 | `pip install marker-pdf`. Optional GPU. CLI, GUI, API available. Surya OCR auto-downloads |
| **Developer Experience** | 88/100 | Excellent CLI and GUI. Optional `--use_llm` for accuracy boost. JSON schema extraction. Multi-format (PDF, DOCX, PPTX, EPUB, images) |
| **Data Sovereignty** | 90/100 | Fully local. Open-source core. GPL/research license. Commercial use requires license from Datalab |
| **Composite** | **87/100** | Best speed/accuracy tradeoff in open-source PDF→Markdown. Choose for batch conversion, multilingual docs, and layout fidelity |

## Architecture & Deployment

Marker is developed by EndlessAI (Datalab). It uses a lightweight model + rules + optional LLM assistance for document conversion. The architecture is designed for speed without sacrificing structure.

**Key architectural features**:
- **Surya OCR**: Built-in OCR engine. Good text recognition. Supports GPU, CPU, and Apple MPS.
- **Layout detection**: Lightweight model detects page layout, reading order, and element types.
- **Formula detection**: Detects and converts mathematical formulas to LaTeX.
- **Image extraction**: Preserves images from PDFs with high quality. Extracts and saves alongside Markdown.
- **Optional LLM boost**: `--use_llm` flag adds a Gemini or Ollama model for accuracy-critical documents. Merges tables across pages, handles inline math, formats tables properly, extracts form values.
- **Multi-format**: PDF, images, DOCX, PPTX, XLSX, HTML, EPUB.

**Deployment options**:
- **Open-source**: `pip install marker-pdf`. Local execution. GPL/research license. Commercial use requires Datalab license.
- **Datalab managed platform**: Hosted API. $5 free credits. Batch processing. SOC 2 Type 2. Zero data retention.
- **Self-hosted API**: Docker container with GPU support. `marker-api` Docker image.
- **Obsidian plugin**: Direct integration with Obsidian vault for knowledge workers.

## Key Features

- **Batch mode**: `marker_chunk_convert` for multiple files on multiple GPUs. `NUM_DEVICES=4 NUM_WORKERS=15` for parallel processing.
- **JSON schema extraction**: Structured extraction with defined JSON schema (beta). Useful for form parsing.
- **Custom formatting**: Extensible with custom formatting and logic via Python API.
- **Pydantic output**: `PdfConverter` returns Pydantic models with typed properties (`markdown`, `metadata`, `images`, `children`, `block_type`).
- **Benchmarking suite**: Built-in benchmarks to compare against cloud services (LlamaParse, Mathpix) and other open-source tools.
- **Multi-language**: All languages. Good CJK support.
- **Hybrid mode**: Marker + LLM together outperforms either alone on table benchmarks.

## Benchmarking

### Accuracy vs. Speed

| Mode | Throughput | Accuracy | Best For |
|------|-----------|----------|----------|
| Standard (CPU/GPU) | ~10-25 pages/sec | Good | General conversion |
| Batch GPU (H100) | ~25 pages/sec | Good | High-volume batch |
| + LLM (`--use_llm`) | ~2-5 pages/sec | Excellent | Accuracy-critical docs |

### Table Benchmark (Marker claims)

| Tool | Table Accuracy | Notes |
|------|---------------|-------|
| Marker + LLM | Highest | Beats cloud services on some benchmarks |
| Marker alone | Good | Better than most open-source tools |
| LlamaParse | Good | Cloud service, comparable |
| Docling | Good | Slightly lower on some benchmarks |

## Pricing (2026)

| Option | Cost | Notes |
|--------|------|-------|
| Open-source (local) | Free | GPL/research license. Commercial use requires Datalab license. |
| Datalab managed | $5 free credits | Pay-as-you-go after. Batch processing. SOC 2. |
| Commercial self-host | Contact Datalab | License for commercial use. |

## When to Use / When to Avoid

**Use Marker when**:
- You need batch conversion of PDFs to Markdown at high throughput
- You need layout-perfect Markdown with heading hierarchy, images, and formulas
- You need GPU-accelerated processing for speed
- You need multi-format support (PDF, DOCX, PPTX, EPUB, images)
- You want the optional LLM boost for accuracy-critical documents
- You need an Obsidian plugin for personal knowledge management
- You are building a data pipeline that needs fast, structured document ingestion

**Avoid Marker when**:
- You need 100% free commercial use without licensing (GPL requires license for commercial self-host; use Docling or PyMuPDF4LLM instead)
- You need the deepest document semantic understanding (Docling's DoclingDocument format is richer)
- You need agentic self-correction (LlamaParse has this)
- You need table accuracy on very complex nested multi-page tables (Docling or LlamaParse may be better)
- You need a managed API with SLAs (use LlamaParse, Reducto, or Datalab managed platform)
- You need built-in MCP server integration (Docling has this; Marker does not yet)

## Known Issues

1. **Commercial license**: The open-source version is GPL/research license. Commercial use requires a license from Datalab. This is a real constraint for commercial products.
2. **Table complexity**: While good, very complex or multi-page tables may need the LLM boost (`--use_llm`) which adds cost and latency.
3. **Surya OCR limitations**: Surya is good but not best-in-class for every language. Some scripts may need verification.
4. **Ecosystem**: Smaller than Docling's ecosystem. Fewer integrations with RAG frameworks (though LangChain and LlamaIndex loaders exist via third parties).

## RAG Pipeline Fit

```
PDF/DOCX/PPTX/EPUB → Marker → Markdown + images + metadata → Chunking → Embedding → Vector DB
```

Marker excels at producing clean, LLM-ready Markdown from complex documents. The image extraction and formula preservation are genuine advantages for technical documents (academic papers, manuals, reports). The batch mode makes it ideal for processing large document corpora.

## License

Open-source: GPL-3.0 / research license. Commercial use requires Datalab license. Managed platform: Proprietary.

## Roster Status

**Tier A** — Best speed/accuracy tradeoff in open-source PDF→Markdown. Retained in Tier A due to GPU batch performance, layout-perfect output, and multi-format support. Watch: commercial license adoption, MCP server, table accuracy on independent benchmarks, ecosystem integration growth.
