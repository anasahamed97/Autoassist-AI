import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.rag import RAGSearchRequest, RAGSearchResponse
from backend.app.rag.retriever import AutomotiveRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG Retrieval"])

# Singleton retriever instance
_retriever: AutomotiveRetriever = None


def get_retriever() -> AutomotiveRetriever:
    global _retriever
    if _retriever is None:
        _retriever = AutomotiveRetriever()
    return _retriever


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic retrieval from automotive service manuals",
    description=(
        "Accepts a customer symptom query (e.g., 'What can cause an engine to overheat?'), "
        "generates an embedding vector locally, and queries Supabase pgvector for the most "
        "relevant automotive documentation chunks and repair procedures."
    ),
)
async def search_automotive_knowledge(request: RAGSearchRequest) -> RAGSearchResponse:
    try:
        retriever = get_retriever()
        filters = {}
        if request.manufacturer:
            filters["manufacturer"] = request.manufacturer
        if request.vehicle_model:
            filters["vehicle_model"] = request.vehicle_model

        response = retriever.search(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            filters=filters if filters else None,
        )
        return response
    except ValueError as ve:
        logger.error("Configuration error during retrieval: %s", ve)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration or Credential Error: {str(ve)}",
        )
    except RuntimeError as re:
        logger.error("Runtime retrieval error: %s", re)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(re),
        )
    except Exception as e:
        logger.error("Unexpected error during RAG retrieval: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during retrieval: {str(e)}",
        )
