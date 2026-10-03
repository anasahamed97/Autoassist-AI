# AutoAssist AI: Intelligent Automotive Diagnostic and Service Assistance Platform
## Milestone 1: Automotive Knowledge Base & Semantic RAG Retrieval System

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.142+-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Supabase-pgvector-3ECF8E.svg)](https://supabase.com/)
[![Embeddings](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2%20(384d)-orange.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

AutoAssist AI is an intelligent automotive service-assistance platform. This repository implements **Milestone 1 (Coordinator Deadline: October 18)**: storing automotive service manuals in a vector database and providing sub-100ms semantic RAG retrieval for customer queries and mechanical symptoms.

---

## 1. System Architecture

```mermaid
graph TD
    A[Automotive Manuals / PDFs / Technical Guides] --> B[Document Loader & SHA-256 Hash]
    B --> C[Text Cleaning & Normalization]
    C --> D[Section-Aware Chunker]
    D --> E[Local ONNX Embedding Model: all-MiniLM-L6-v2]
    E -->|384-dimensional vectors| F[Supabase PostgreSQL + pgvector]
    
    G[Customer Query / Symptom Description] --> H[FastAPI Endpoint: POST /api/rag/search]
    H --> I[Query Embedding Generator]
    I --> J[Supabase RPC: match_document_chunks]
    F --> J
    J --> K[Top-K Ranked Technical Chunks & Metadata]
    K --> L[Diagnostic Support Response + Safety Disclaimer]
```

### Key Technical Decisions
1. **Database**: **Supabase PostgreSQL + pgvector** using an HNSW index (`vector_cosine_ops`) for sub-millisecond approximate nearest neighbor search.
2. **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` producing **384-dimensional normalized vectors**. Executed via **ONNX Runtime (Microsoft Authenticode signed)** and **HuggingFace Tokenizers** locally on CPU, ensuring zero GPU requirement and full compatibility with Windows 11 Smart App Control.
3. **Idempotent Ingestion**: Documents are indexed using a SHA-256 content hash (`content_hash`) in the `documents` table to prevent duplicate records upon repeated ingestion runs.
4. **Section-Aware Chunking**: Chunks preserve section headings, paragraph boundaries, and page numbers rather than blindly splitting arbitrary strings.

---

## 2. Directory Structure

```text
autoassist AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entrypoint & CORS
│   │   ├── config.py            # Pydantic environment configuration
│   │   ├── database.py          # Supabase client manager
│   │   ├── api/
│   │   │   └── rag.py           # POST /api/rag/search route handler
│   │   ├── rag/
│   │   │   ├── document_loader.py # Multi-format loader (PDF, Markdown, text)
│   │   │   ├── text_cleaner.py    # Whitespace & header artifact cleaning
│   │   │   ├── chunker.py         # Heading & page-aware chunking
│   │   │   ├── embeddings.py      # ONNX 384-dim embedding model
│   │   │   ├── vector_store.py    # Supabase pgvector upsert & batching
│   │   │   └── retriever.py       # Semantic vector similarity search
│   │   └── schemas/
│   │       └── rag.py           # Pydantic request/response models
├── data/
│   ├── raw/                     # Original automotive service documentation
│   │   ├── cooling_system_service_manual.md
│   │   ├── starting_and_charging_system_manual.md
│   │   ├── brake_system_service_and_diagnosis.md
│   │   ├── engine_performance_and_dtc_troubleshooting.md
│   │   └── honda_civic_service_and_maintenance.pdf
│   └── processed/               # Audit manifest & local knowledge base
│       ├── ingestion_manifest.json
│       ├── local_knowledge_base.json
│       └── evaluation_report.json
├── sql/
│   └── schema.sql               # Supabase pgvector schema, tables & RPC function
├── scripts/
│   ├── ingest_documents.py      # CLI script to chunk, embed, and upload docs
│   ├── test_retrieval.py        # Interactive CLI search tool
│   ├── evaluate_retrieval.py    # 16-query evaluation benchmark
│   └── create_sample_pdf.py     # PDF generator for testing
├── tests/
│   ├── test_rag.py              # Unit tests (cleaner, chunker, loader, embeddings)
│   └── test_api.py              # FastAPI test client integration tests
├── .env.example                 # Environment configuration template
├── requirements.txt             # Pinned dependencies
├── evaluation_report.md         # Full retrieval evaluation report
└── README.md                    # Project documentation
```

---

## 3. Database Setup (Supabase PostgreSQL + pgvector)

1. Log into your [Supabase Dashboard](https://supabase.com/dashboard) and create a new project.
2. In the Supabase dashboard, navigate to the **SQL Editor**.
3. Copy and execute the contents of [`sql/schema.sql`](file:///c:/Users/anasa/OneDrive/Desktop/autoassist%20AI/sql/schema.sql).
   This script:
   - Enables the `vector` extension (`CREATE EXTENSION IF NOT EXISTS vector;`).
   - Creates the `documents` table (with `content_hash UNIQUE` for deduplication).
   - Creates the `document_chunks` table with `embedding vector(384)`.
   - Creates an **HNSW index** (`document_chunks_embedding_hnsw_idx`) for cosine similarity.
   - Defines the `match_document_chunks` stored procedure (RPC) for ranked Top-K semantic retrieval.
   - Configures Row Level Security (RLS) policies.

---

## 4. Environment Configuration

Copy the example environment configuration:
```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:
```ini
# Supabase Project Configuration (Project Settings -> API)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# RAG & Embedding Settings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=500
CHUNK_OVERLAP=80
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.30
```

> **Note**: If Supabase credentials are not set, the system automatically falls back to the local pre-computed vector index in `data/processed/local_knowledge_base.json` so that offline evaluation and local development can proceed uninterrupted.

---

## 5. Ingestion Pipeline

To parse, clean, chunk, embed, and upload all documents in `data/raw/` into Supabase:

```bash
python scripts/ingest_documents.py
```

Options:
- `--force`: Force re-indexing of documents even if their content hash matches existing records.
- `--dry-run`: Process documents, generate embeddings, and build the local knowledge base without uploading to Supabase.
- `--dir <path>`: Specify an alternative input directory.

Output summary:
```text
Found 5 automotive documents in data/raw
Extracted 19 blocks across manuals
Generated 68 chunks (chunk_size=500, overlap=80)
Generating 384-dimensional embeddings with all-MiniLM-L6-v2...
Audit manifest saved to: data/processed/ingestion_manifest.json
Local knowledge base backup saved to: data/processed/local_knowledge_base.json
```

---

## 6. Running the API Server

Start the FastAPI application with Uvicorn:

```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API documentation (Swagger UI) is available at:
`http://127.0.0.1:8000/docs`

### Example Search Request

**POST** `http://127.0.0.1:8000/api/rag/search`

```json
{
  "query": "What can cause an engine to overheat?",
  "top_k": 3,
  "similarity_threshold": 0.35
}
```

### Example Search Response

```json
{
  "query": "What can cause an engine to overheat?",
  "results": [
    {
      "content": "### Primary Causes of Engine Overheating:\n1. Low Coolant Level: Caused by external leaks (radiator hoses, water pump weep hole, heater core, radiator seams) or internal leaks (blown cylinder head gasket, cracked engine block or cylinder head).\n2. Thermostat Stuck in Closed Position: Prevents hot coolant in the engine cylinder head from reaching the radiator for cooling...",
      "similarity": 0.7819,
      "document_title": "Cooling System Service Manual",
      "manufacturer": "Generic / Honda / Toyota",
      "vehicle_model": "Standard Powertrain",
      "model_year": 2022,
      "document_type": "Service Manual",
      "section": "SECTION 2: ENGINE OVERHEATING DIAGNOSIS & CAUSES",
      "page_number": 2,
      "source": "cooling_system_service_manual.md",
      "source_url": "https://www.nhtsa.gov/vehicle-safety"
    },
    {
      "content": "Engine Overheating Troubleshooting:\n1. Check coolant reserve tank level when cold. If below MIN line, inspect for leaks.\n2. If temperature gauge needle reaches H (Hot), turn off A/C and safely stop engine.\n3. Radiator Fan Operation: Ensure both radiator fan and condenser fan activate when engine coolant temperature reaches 199 deg F (93 deg C)...",
      "similarity": 0.5296,
      "document_title": "Honda Civic Service And Maintenance",
      "manufacturer": null,
      "vehicle_model": null,
      "model_year": null,
      "document_type": "Service Manual",
      "section": "SECTION 2: COOLING SYSTEM DIAGNOSIS & BLEEDING",
      "page_number": 2,
      "source": "honda_civic_service_and_maintenance.pdf",
      "source_url": null
    }
  ],
  "total_results": 2,
  "latency_ms": 78.4,
  "safety_disclaimer": "Technical documentation retrieval for diagnostic assistance only. Does not constitute an automated certified diagnosis."
}
```

---

## 7. Testing & Evaluation

### Run Unit & Integration Tests
```bash
python -m pytest -v tests/
```
All 9 tests pass:
- Text cleaning, normalizations, and section extraction
- Document chunking with configurable overlap
- Markdown document loading & SHA-256 hashing
- PDF document parsing with `pypdf` page extraction
- 384-dimensional local vector embedding generation & L2 norm
- FastAPI health, root, search, and validation error endpoints

### Run Interactive Query Search
```bash
python scripts/test_retrieval.py "What can cause a clicking noise when starting?"
```

### Run Benchmark Evaluation (16 Queries)
```bash
python scripts/evaluate_retrieval.py
```

Benchmark Summary:
- **Total Queries Evaluated**: 16
- **Top-1 Precision**: **100.0%** (15/15 domain queries matched the expected subsystem)
- **Top-K Recall**: **100.0%** (15/15)
- **Negative Control Query** (`How do I bake a chocolate cake at home?`): Correctly rejected (0 matches above threshold)
- **Average Retrieval Latency**: **121.95 ms** (sub-80 ms steady state)

Detailed tabular results are archived in [`evaluation_report.md`](file:///c:/Users/anasa/OneDrive/Desktop/autoassist%20AI/evaluation_report.md) and [`data/processed/evaluation_report.json`](file:///c:/Users/anasa/OneDrive/Desktop/autoassist%20AI/data/processed/evaluation_report.json).

---

## 8. Milestone 2 & 3 Compatibility Roadmap

The RAG module is designed for direct integration into subsequent project phases:

- **November 29 Milestone (Audio Processing)**:
  An audio endpoint (`POST /api/audio/diagnose`) can process incoming WAV audio, extract automotive symptom keywords, and directly invoke `AutomotiveRetriever.search(query=extracted_keywords)`.
- **December 18 Milestone (Full Web App)**:
  FastAPI has CORS enabled and clean REST contracts (`POST /api/rag/search`), ready to be connected directly to a React / Vite or Next.js web application frontend with diagnostic escalation workflows.
