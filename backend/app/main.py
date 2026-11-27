import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.api.rag import router as rag_router
from backend.app.api.analyzers import router as analyzers_router
from backend.app.api.vehicles import router as vehicles_router
from backend.app.api.pricing import router as pricing_router
from backend.app.api.quotations import router as quotations_router
from backend.app.api.maintenance import router as maintenance_router
from backend.app.api.severity import router as severity_router
from backend.app.api.voice import router as voice_router

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autoassist.api")

app = FastAPI(
    title="AutoAssist AI - Automotive Diagnostic & Service Assistance Platform",
    description=(
        "Production Automotive Diagnostic Intelligence & RAG Platform. "
        "Allows querying automotive service manuals, diagnostic trouble codes (DTC), "
        "and running specialized problem analyzers for electrical, thermal, acoustic, "
        "braking, transmission, and emissions systems."
    ),
    version="2.0.0",
)

# Enable CORS for web development and cross-origin clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(rag_router)
app.include_router(analyzers_router)
app.include_router(vehicles_router)
app.include_router(pricing_router)
app.include_router(quotations_router)
app.include_router(maintenance_router)
app.include_router(severity_router)
app.include_router(voice_router)

# Mount static web assets if directory exists
if settings.static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")


@app.get("/", tags=["General"])
async def root(request: Request):
    """
    Serves the modern AutoAssist AI diagnostic web application when accessed from a web browser,
    or returns API metadata JSON when called by API clients.
    """
    accept = request.headers.get("accept", "")
    index_file = settings.static_dir / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(index_file)

    return {
        "platform": "AutoAssist AI",
        "milestone": "Full Automotive Diagnostic, Cost Estimation & Service Assistance Platform",
        "status": "online",
        "embedding_model": settings.embedding_model_name,
        "embedding_dimension": settings.embedding_dimension,
        "docs_url": "/docs",
        "website_url": "/",
        "endpoints": {
            "search": "POST /api/rag/search",
            "explain_manual": "POST /api/rag/explain",
            "vehicles": "GET/POST/PUT/DELETE /api/vehicles",
            "pricing_estimate": "POST /api/pricing/estimate",
            "quotations_evaluate": "POST /api/quotations/evaluate",
            "maintenance_overview": "GET /api/maintenance/overview",
            "severity_assess": "POST /api/severity/assess",
            "analyzers_catalog": "GET /api/analyzers/catalog",
            "dtc_analyzer": "POST /api/analyzers/dtc",
            "electrical_analyzer": "POST /api/analyzers/electrical",
            "thermal_analyzer": "POST /api/analyzers/thermal",
            "acoustic_analyzer": "POST /api/analyzers/acoustic",
            "brake_analyzer": "POST /api/analyzers/brake",
            "drivetrain_analyzer": "POST /api/analyzers/drivetrain",
            "emissions_analyzer": "POST /api/analyzers/emissions",
            "wizard_start": "POST /api/analyzers/wizard/start",
            "wizard_step": "POST /api/analyzers/wizard/step",
            "price_guide": "GET /api/analyzers/repairs/price-guide",
            "health": "GET /health",
        },
    }


@app.get("/app", response_class=FileResponse, tags=["General"])
async def web_app():
    """Explicit endpoint to serve the single-page web dashboard."""
    index_file = settings.static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=404,
        content={"error": "Web application static assets not found."}
    )


@app.get("/health", tags=["General"])
async def health_check():
    supabase_configured = bool(settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key))
    return {
        "status": "healthy",
        "database": "supabase_pgvector" if supabase_configured else "local_onnx_knowledge_base",
        "supabase_configured": supabase_configured,
        "embedding_dimension": settings.embedding_dimension,
        "analyzers_count": 8,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
