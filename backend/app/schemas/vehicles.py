from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class VehicleBase(BaseModel):
    make: str = Field(..., min_length=1, description="Vehicle manufacturer, e.g. Honda")
    model: str = Field(..., min_length=1, description="Vehicle model, e.g. Civic")
    year: int = Field(..., ge=1970, le=2030, description="Manufacturing year")
    fuel_type: str = Field(default="Petrol", description="Fuel type: Petrol, Diesel, CNG, Hybrid, Electric")
    engine_variant: Optional[str] = Field(default=None, description="Engine specification, e.g. 1.5L i-VTEC")
    nickname: Optional[str] = Field(default=None, description="Personal nickname for vehicle")
    odometer: int = Field(default=45000, ge=0, description="Current odometer reading in km or miles")
    is_default: bool = Field(default=False, description="Whether this is the user's primary vehicle")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1970, le=2030)
    fuel_type: Optional[str] = None
    engine_variant: Optional[str] = None
    nickname: Optional[str] = None
    odometer: Optional[int] = Field(None, ge=0)
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class VehicleOut(VehicleBase):
    id: str
    user_id: str = "default_user"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
