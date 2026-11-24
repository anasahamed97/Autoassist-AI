# AutoAssist AI — Deployment & Infrastructure Guide

This guide provides instructions for deploying **AutoAssist AI** to production cloud environments, configuring Supabase PostgreSQL + pgvector, and setting up automated CI/CD testing.

---

## 1. Environment Variables Specification

| Variable | Required | Default | Description |
|---|---|---|---|
| `SUPABASE_URL` | **Yes** | — | Supabase Project REST URL (`https://xyz.supabase.co`) |
| `SUPABASE_KEY` | **Yes** | — | Supabase Public `anon` API Key |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | — | Supabase `service_role` Secret Key (for backend server operations) |
| `EMBEDDING_MODEL_NAME` | No | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model ID |
| `EMBEDDING_DIMENSION` | No | `384` | Vector dimension for pgvector embeddings |
| `CHUNK_SIZE` | No | `500` | Character chunk size for technical document chunking |
| `CHUNK_OVERLAP` | No | `80` | Overlap character count between consecutive chunks |
| `RAG_TOP_K` | No | `5` | Maximum number of chunks returned per query |
| `RAG_SIMILARITY_THRESHOLD` | No | `0.25` | Minimum cosine similarity threshold |
| `API_HOST` | No | `0.0.0.0` | API bind address |
| `API_PORT` | No | `8000` | Port for the FastAPI server |

---

## 2. Supabase Database Setup & Migrations

In the Supabase Project Dashboard, navigate to the **SQL Editor** and execute the following scripts in order:

1. **`sql/schema.sql`**:
   - Enables `vector` extension.
   - Creates `public.documents` and `public.document_chunks`.
   - Creates HNSW index (`document_chunks_embedding_hnsw_idx`).
   - Creates the `match_document_chunks` RPC similarity search function.

2. **`sql/schema_v2.sql`**:
   - Creates `public.vehicles` profile table.
   - Creates `public.repair_pricing` structured benchmark table with initial seed data.
   - Creates `public.mechanic_quotations` table.
   - Creates `public.maintenance_records` table.

3. **`sql/schema_v3_rls.sql`**:
   - Enables Row Level Security (RLS) on all tables.
   - Establishes user isolation policies (`auth.uid() = user_id::uuid`).
   - Grants public read access to `repair_pricing` benchmarks and technical documents.
   - Grants `service_role` administrative access for backend service operations.

---

## 3. Docker Deployment

### 3.1 Build the Production Image
```bash
docker build -t autoassist-ai:latest .
```

### 3.2 Run Container
```bash
docker run -d \
  --name autoassist-ai \
  -p 8000:8000 \
  --env-file .env \
  autoassist-ai:latest
```

### 3.3 Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: autoassist-ai
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```
Run with:
```bash
docker compose up -d
```

---

## 4. Cloud Platform Deployments

### Render.com
1. Create a new **Web Service** connected to your repository.
2. Select **Python 3** environment.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables: `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.

### Railway.app
1. Deploy from GitHub repository.
2. Railway detects Dockerfile or `requirements.txt`.
3. Add environment variables in Railway settings.

### Fly.io
```bash
fly launch
fly secrets set SUPABASE_URL="..." SUPABASE_KEY="..." SUPABASE_SERVICE_ROLE_KEY="..."
fly deploy
```

---

## 5. Production Health Check

Verify deployment health:
```bash
curl -f http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "AutoAssist AI Platform",
  "version": "2.0.0"
}
```
