import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends

from backend.app.schemas.maintenance import (
    MaintenanceOverview,
    MaintenanceRecordCreate,
    MaintenanceRecordOut,
)
from backend.app.services.maintenance_service import get_maintenance_service
from backend.app.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["Vehicle Maintenance Tracking"])


@router.get("/overview", response_model=MaintenanceOverview, summary="Get maintenance overview & reminders")
async def get_maintenance_overview(
    vehicle_id: Optional[str] = None,
    current_odometer: int = 45000,
    user_id: str = Depends(get_current_user_id),
):
    service = get_maintenance_service()
    return service.get_overview(vehicle_id=vehicle_id, current_odometer=current_odometer, user_id=user_id)


@router.post("/records", response_model=MaintenanceRecordOut, status_code=status.HTTP_201_CREATED, summary="Add maintenance record")
async def add_maintenance_record(
    record: MaintenanceRecordCreate,
    user_id: str = Depends(get_current_user_id)
):
    service = get_maintenance_service()
    return service.add_record(record, user_id=user_id)


@router.post("/records/{record_id}/complete", response_model=MaintenanceRecordOut, summary="Mark maintenance service completed")
async def mark_service_completed(
    record_id: str,
    current_odometer: int = 45000,
    user_id: str = Depends(get_current_user_id),
):
    service = get_maintenance_service()
    rec = service.mark_completed(record_id, current_odometer=current_odometer, user_id=user_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Maintenance record '{record_id}' not found or access denied.")
    return rec
