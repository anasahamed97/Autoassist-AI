import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.severity import SeverityRequest, SeverityResponse
from backend.app.services.severity_service import get_severity_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/severity", tags=["Problem Severity Assessment"])


@router.post("/assess", response_model=SeverityResponse, summary="Assess automotive problem severity & road safety")
async def assess_problem_severity(request: SeverityRequest):
    try:
        service = get_severity_service()
        return service.assess_severity(request)
    except Exception as e:
        logger.error("Severity assessment error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Severity assessment failed: {str(e)}"
        )
