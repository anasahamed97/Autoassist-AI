import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.quotations import QuoteComparisonRequest, QuoteComparisonResponse
from backend.app.services.quotation_service import get_quotation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quotations", tags=["Mechanic Quotation Checker"])


@router.post("/evaluate", response_model=QuoteComparisonResponse, summary="Evaluate mechanic quotation against benchmarks")
async def evaluate_quotation(request: QuoteComparisonRequest):
    try:
        service = get_quotation_service()
        return service.evaluate_quotation(request)
    except Exception as e:
        logger.error("Quotation evaluation error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quotation evaluation failed: {str(e)}"
        )
