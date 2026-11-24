import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.vehicles import VehicleCreate, VehicleUpdate, VehicleOut
from backend.app.services.vehicle_service import get_vehicle_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vehicles", tags=["Vehicle Profile Management"])


@router.get("", response_model=List[VehicleOut], summary="List user vehicle profiles")
async def list_vehicles(user_id: str = "default_user"):
    service = get_vehicle_service()
    return service.list_vehicles(user_id=user_id)


@router.get("/default", response_model=Optional[VehicleOut], summary="Get default active vehicle")
async def get_default_vehicle(user_id: str = "default_user"):
    service = get_vehicle_service()
    veh = service.get_default_vehicle(user_id=user_id)
    if not veh:
        raise HTTPException(status_code=404, detail="No vehicle profile found.")
    return veh


@router.get("/{vehicle_id}", response_model=VehicleOut, summary="Get single vehicle profile")
async def get_vehicle(vehicle_id: str):
    service = get_vehicle_service()
    veh = service.get_vehicle(vehicle_id)
    if not veh:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")
    return veh


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED, summary="Create vehicle profile")
async def create_vehicle(vehicle: VehicleCreate, user_id: str = "default_user"):
    service = get_vehicle_service()
    return service.create_vehicle(vehicle, user_id=user_id)


@router.put("/{vehicle_id}", response_model=VehicleOut, summary="Update vehicle profile or mileage")
async def update_vehicle(vehicle_id: str, updates: VehicleUpdate, user_id: str = "default_user"):
    service = get_vehicle_service()
    veh = service.update_vehicle(vehicle_id, updates, user_id=user_id)
    if not veh:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")
    return veh


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete vehicle profile")
async def delete_vehicle(vehicle_id: str):
    service = get_vehicle_service()
    success = service.delete_vehicle(vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")
    return None
