# LlamaParse

LlamaIndex's managed document parsing service. Agentic OCR with layout-aware semantic reconstruction. Built for the LlamaIndex ecosystem but usable standalone.

## TL;DR

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Accuracy** | 92/100 | Agentic self-correction loop. Semantic reconstruction. 90%+ pass-through rate vs. 60-70% legacy OCR. Best table accuracy on complex enterprise docs |
| **Speed** | 75/100 | Tiered pricing: Fast (1 credit), Cost-effective (3), Agentic (10), Agentic Plus (45). Slower modes = higher accuracy |
| **Token Economics** | 72/100 | 10,000 free credits/mo. Cost-effective: ~$0.003/page. Agentic: ~$0.01/page. Agentic Plus: ~$0.09/page. Costs add up at scale |
| **Scale** | 85/100 | 500M+ documents processed. 300K+ LlamaCloud users. Batch processing. Enterprise VPC deployment |
| **Ops Burden** | 88/100 | Zero infrastructure. API-only. Python/TypeScript SDKs. CLI tool. Web sandbox |
| **Developer Experience** | 88/100 | Native LlamaIndex integration. Clean SDK. Sandbox for testing. HIPAA/SOC 2/GDPR compliant |
| **Data Sovereignty** | 60/100 | Cloud API. Enterprise VPC option. 48-hour cache by default. No true self-host option |
| **Composite** | **80/100** | Best managed parser for complex enterprise documents. The LlamaIndex-native choice. Cost scales with accuracy tier |

## Architecture & Deployment

LlamaParse is a cloud service, not a local library. It uses vision-language models and agentic workflows to parse documents with semantic understanding rather than simple text extraction.

**Key architectural features**:
- **Agentic self-correction**: When initial extraction is uncertain, LlamaParse reruns with adjusted parameters automatically. Multi-pass parsing loop.
- **Semantic reconstruction**: Understands heading hierarchy, table structure, figure context, and section boundaries. Output is clean Markdown optimized for LLM consumption.
- **Tiered parsing modes**: Four accuracy/speed trade-offs:
  - **Fast (1 credit)**: Quick extraction. Good for simple digital PDFs.
  - **Cost-effective (3 credits)**: Balanced. The default recommendation.
  - **Agentic (10 credits)**: Multi-pass with self-correction. Complex tables, charts, embedded images.
  - **Agentic Plus (45-90 credits)**: Top-tier models. Maximum accuracy. $0.09/page.
- **Cost optimizer**: Routes simple pages to faster, cheaper extraction automatically.
- **LiteParse**: Open-source CLI (March 2026) for agent-native local parsing. Apache 2.0. TypeScript-native with Python wrapper. Tesseract.js OCR.

**Deployment options**:
- **Cloud API (SaaS)**: Primary offering. Secure SaaS in NA/EU. Enterprise VPC on AWS/Azure/GCP.
- **LiteParse (local)**: `npm i -g @llamaindex/liteparse` or `pip install liteparse`. Fully local, zero cloud. Tesseract.js OCR.
- **AWS Marketplace / Azure Marketplace**: Enterprise deployment.

## Key Features

- **90+ formats**: PDF, DOCX, PPTX, XLSX, HTML, images, and more.
- **100+ languages**: Multilingual support including CJK, Arabic, and Indic scripts.
- **Layout extraction**: Bounding boxes for page elements (tables, figures, titles, text, lists). Optional `extract_layout`.
- **Multimodal**: Extracts and describes images, charts, and figures. Not just text.
- **LlamaExtract**: Schema-driven structured extraction (deprecated in LlamaParse; moved to dedicated service).
- **MCP support**: Rebuilt MCP server (2026). Integration with Claude, Cursor, VS Code.
- **Compliance**: HIPAA, SOC 2 Type II, GDPR. BAA available for Enterprise. Data encrypted in transit and at rest.

## Pricing (2026)

| Tier | Credits/Page | Approx. Cost/Page | Notes |
|------|-------------|-------------------|-------|
| Fast | 1 | ~$0.001 | Simple digital PDFs |
| Cost-effective | 3 | ~$0.003 | Default recommendation |
| Agentic | 10 | ~$0.01 | Complex tables, charts, images |
| Agentic Plus | 45-90 | ~$0.056-0.11 | Maximum accuracy, premium models |
| Layout extraction | +extra | +~$0.001-0.003 | Bounding boxes per page |

**Free tier**: 10,000 credits/month on signup. 7,000 pages/week on starter plan.

**Enterprise**: Private VPC, custom models, dedicated support, volume discounts.

## When to Use / When to Avoid

**Use LlamaParse when**:
- Your pipeline is already built on LlamaIndex
- You need the highest accuracy on complex enterprise documents (financial, legal, insurance, healthcare)
- You need table extraction on nested, multi-page, or non-standard tables
- You want agentic self-correction without building it yourself
- You need multimodal parsing (images, charts, figures alongside text)
- You need HIPAA/SOC 2 compliance without managing infrastructure

**Avoid LlamaParse when**:
- You need 100% local/air-gapped processing (use Docling or LiteParse)
- Your budget is tight and you process >100K pages/month (costs add up)
- Your documents are simple digital PDFs (Docling or PyMuPDF4LLM are free and sufficient)
- You are not using LlamaIndex and don't want ecosystem lock-in
- You need editing/form-filling capabilities (Reducto has this)
- You need the fastest possible parsing (Fast mode is still API-bound; local tools are faster)

## RAG Pipeline Fit

```
PDF/DOCX/PPTX → LlamaParse → Markdown/JSON → LlamaIndex Document → Chunking → Embedding → Vector DB
```

The native integration with LlamaIndex means documents parse directly into `Document` objects ready for indexing. This removes one transformation step from the pipeline. For non-LlamaIndex users, the Markdown output is framework-agnostic.

## License

Cloud API: Proprietary. LiteParse: Apache 2.0.

## Roster Status

**Tier A** — Best managed parser for complex enterprise documents. Retained in Tier A due to agentic accuracy, LlamaIndex ecosystem integration, and compliance posture. Watch: LiteParse adoption, pricing transparency at scale, non-LlamaIndex ecosystem expansion.
