import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.api.rag import router as rag_router

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autoassist.api")

app = FastAPI(
    title="AutoAssist AI - Automotive Diagnostic & Service Assistance Platform",
    description=(
        "Backend RAG Retrieval & Knowledge API (Milestone 1). "
        "Allows querying automotive service manuals, diagnostic trouble codes (DTC), "
        "and maintenance guides via local sentence embeddings and Supabase pgvector."
    ),
    version="1.0.0",
)

# Enable CORS for local web development (Milestone 3 compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register RAG retrieval router
app.include_router(rag_router)


@app.get("/", tags=["General"])
async def root():
    return {
        "platform": "AutoAssist AI",
        "milestone": "Milestone 1 - RAG Knowledge & Retrieval System",
        "status": "online",
        "embedding_model": settings.embedding_model_name,
        "embedding_dimension": settings.embedding_dimension,
        "docs_url": "/docs",
        "endpoints": {
            "search": "POST /api/rag/search",
            "health": "GET /health",
        },
    }


@app.get("/health", tags=["General"])
async def health_check():
    supabase_configured = bool(settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key))
    return {
        "status": "healthy",
        "database": "supabase_pgvector",
        "supabase_configured": supabase_configured,
        "embedding_dimension": settings.embedding_dimension,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
