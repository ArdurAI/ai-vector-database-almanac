# Unstructured

A modular document parsing platform that transforms unstructured documents into structured data elements. 30+ formats, flexible pipelines, and both open-source and managed API options.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 78/100 | Good on standard documents. Average on complex tables. Hi-res strategy uses Detectron2/YOLOX for layout. Modular but not best-in-class on any single dimension |
| **Speed** | 65/100 | Fast strategy: $1/1K pages, quick but basic. Hi-res: $10/1K pages, model-based, slow. 700-page PDF can take 1 hour on CPU hi-res |
| **Token Economics** | 85/100 | Open-source: free. SaaS API: $1/1K pages (fast), $10/1K pages (hi-res). AWS/Azure marketplace VPC deployment |
| **Scale** | 80/100 | SaaS API scales. Open-source self-hosted for large batch. AWS/Azure marketplace for VPC. No distributed processing |
| **Ops Burden** | 75/100 | Open-source: `pip install unstructured[all-docs]`. Heavy dependencies (~2GB). SaaS: zero ops |
| **Developer Experience** | 82/100 | Good Python API. Multiple strategies (fast, hi_res, ocr_only). Element-typed output. LangChain native loader. Docs are solid |
| **Data Sovereignty** | 85/100 | Open-source runs locally. SaaS is cloud. VPC option via AWS/Azure marketplace. Flexible deployment |
| **Composite** | **78/100** | The flexible workhorse. Not the best at any single task but covers the most formats and deployment options. Good default for diverse document types |

## Architecture & Deployment

Unstructured is a modular pipeline. Documents pass through partitioners (PDF, DOCX, image, etc.), each with strategies (fast, hi_res, ocr_only), and output typed elements (Title, NarrativeText, Table, Image, etc.).

**Key architectural features**:
- **Partitioners**: Per-format document splitters. PDF partitioner uses PDFPlumber or PyMuPDF. Image partitioner uses OCR.
- **Strategies**:
  - `fast`: Rule-based NLP extraction. Quick but misses layout and images. Good for native digital PDFs.
  - `hi_res`: Layout detection via Detectron2 or YOLOX. Model-based. Slower but catches tables, images, reading order. Good for scanned or complex documents.
  - `ocr_only`: OCR for image-based files. No layout detection.
- **Element typing**: Output is a list of typed elements: `Title`, `NarrativeText`, `ListItem`, `Table`, `Image`, `Header`, `Footer`, `FigureCaption`, etc. Not just text — structured data.
- **Chunking strategies**: `by-title`, `by-section`, `basic`, `sliding-window`. Uses detected structure for semantic chunking.

**Deployment options**:
- **Open-source library**: `pip install unstructured[all-docs]`. Local execution. Heavy install (~2GB with all dependencies).
- **SaaS API**: `unstructured-client`. Hosted API. Fast: $1/1K pages. Hi-res: $10/1K pages.
- **AWS/Azure Marketplace**: VPC deployment for compliance-sensitive workloads.
- **Docker**: Self-hosted API server in container.

## Key Features

- **30+ formats**: PDF, DOCX, PPTX, XLSX, HTML, EML, images, and more.
- **Element-typed output**: Structured JSON with element types. Easy to filter (e.g., drop headers/footers, keep only tables).
- **Table detection**: `infer_table_structure=True` with YOLOX for table extraction. Moderate accuracy on complex tables.
- **Image extraction**: Extracts images from PDFs and documents. Can caption images with VLM.
- **Chunking**: `chunk_by_title()` preserves section boundaries. Better than naive sliding window for RAG.
- **LangChain integration**: `UnstructuredFileLoader` and `UnstructuredPDFLoader`. Standard LangChain document loaders.
- **GPU strategy**: `hi_res` with GPU acceleration for layout detection. Significant speedup on complex documents.

## Pricing (2026)

| Strategy | Cost | Speed | Accuracy | Best For |
|----------|------|-------|----------|----------|
| Fast | $1/1K pages | Fast | Basic | Native digital PDFs, simple docs |
| Hi-res | $10/1K pages | Slow | Good | Scanned docs, complex layouts, tables |
| OCR-only | $10/1K pages | Slow | OCR-only | Image-based files (PNG, JPG, scanned PDFs) |
| GPU hi-res | Variable | Medium | Better | Complex layouts with GPU acceleration |

## When to Use / When to Avoid

**Use Unstructured when**:
- You need to parse 30+ different formats in one pipeline
- You want element-typed output (not just text) for downstream filtering
- You need flexible chunking strategies (by-title, by-section)
- You want both open-source and managed API options
- You need VPC deployment for compliance (AWS/Azure marketplace)
- You are building a custom ETL pipeline and need modular components

**Avoid Unstructured when**:
- You need the highest table accuracy (Docling or LlamaParse are better)
- You need the fastest parsing on simple documents (PyMuPDF4LLM or Marker are faster)
- You need agentic self-correction (LlamaParse or Reducto have this)
- You need multimodal VLM understanding (Granite-Docling or LlamaParse are better)
- You need the simplest API (PyMuPDF4LLM is a single pip install and one function call)
- You are processing 1M+ pages/month on SaaS (cost becomes significant; self-host open-source)

## Known Issues

1. **Speed on hi-res**: The hi_res strategy with Detectron2/YOLOX is genuinely slow. A 700-page PDF on CPU without GPU can take over 1 hour. GPU acceleration is recommended for production.
2. **Complex table accuracy**: Unstructured's table detection is good but not best-in-class. Nested tables, merged cells, and multi-page tables often require post-processing.
3. **Heavy dependencies**: The open-source library with `all-docs` extras is ~2GB. This includes PyTorch, Transformers, Detectron2, and Tesseract. Docker is recommended for deployment.
4. **SaaS vs. OSS gap**: The SaaS API is more capable than the open-source version in some cases (newer models, better OCR). The open-source version may lag behind.

## RAG Pipeline Fit

```
Document (any format) → Unstructured partition → Element list (JSON) → Filter elements → Chunk (by-title) → Embedding → Vector DB
```

Unstructured's element typing enables sophisticated preprocessing: drop headers/footers, extract tables for special handling, caption images separately, and chunk by document section rather than sliding window.

## License

Open-source: Apache 2.0. SaaS API: Proprietary.

## Roster Status

**Tier A** — The flexible workhorse with the widest format coverage. Retained in Tier A due to 30+ format support, element-typed output, and flexible deployment options. Watch: hi-res speed improvements, table accuracy on real-world benchmarks, SaaS vs. open-source parity.
