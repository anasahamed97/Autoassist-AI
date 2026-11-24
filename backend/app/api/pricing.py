import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.pricing import RepairPricingItem, RepairEstimateRequest, RepairEstimateResponse
from backend.app.services.pricing_service import get_pricing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pricing", tags=["Repair Cost Estimator"])


@router.get("/catalog", response_model=List[Dict[str, Any]], summary="List standard repair pricing catalog")
async def get_pricing_catalog(category: Optional[str] = None):
    service = get_pricing_service()
    return service.list_catalog(category=category)


@router.post("/estimate", response_model=RepairEstimateResponse, summary="Calculate vehicle repair cost estimate")
async def estimate_repair(request: RepairEstimateRequest):
    try:
        service = get_pricing_service()
        return service.estimate_repair_cost(request)
    except Exception as e:
        logger.error("Cost estimation error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repair cost estimation failed: {str(e)}"
        )
