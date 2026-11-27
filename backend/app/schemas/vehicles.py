from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class VehicleBase(BaseModel):
    make: str = Field(..., min_length=1, description="Vehicle manufacturer, e.g. Honda")
    model: str = Field(..., min_length=1, description="Vehicle model, e.g. Civic")
    year: int = Field(..., ge=1970, le=2030, description="Manufacturing year")
    fuel_type: str = Field(default="Petrol", description="Fuel type: Petrol, Diesel, CNG, Hybrid, Electric")
    engine_variant: Optional[str] = Field(default=None, description="Engine specification, e.g. 1.5L i-VTEC")
    nickname: Optional[str] = Field(default=None, description="Personal nickname for vehicle")
    odometer: int = Field(default=45000, ge=0, description="Current odometer reading in km")
    mileage_km: Optional[int] = Field(default=None, ge=0, description="Alias for odometer in km")
    city: Optional[str] = Field(default="Bengaluru", description="Operating city for repair rates")
    is_default: bool = Field(default=False, description="Whether this is the user's primary vehicle")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def sync_mileage_and_city(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync mileage_km and odometer
            if "mileage_km" in data and data["mileage_km"] is not None:
                if "odometer" not in data or data["odometer"] is None:
                    data["odometer"] = data["mileage_km"]
                else:
                    data["mileage_km"] = data["odometer"]
            elif "odometer" in data and data["odometer"] is not None:
                data["mileage_km"] = data["odometer"]

            # Sync city and metadata
            meta = dict(data.get("metadata") or {})
            if "city" in data and data["city"]:
                meta["city"] = data["city"]
            elif "city" in meta and meta["city"]:
                data["city"] = meta["city"]
            else:
                data["city"] = meta.get("city", "Bengaluru")
                meta["city"] = data["city"]
            data["metadata"] = meta
        return data


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
    mileage_km: Optional[int] = Field(None, ge=0)
    city: Optional[str] = None
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def sync_update_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "mileage_km" in data and data["mileage_km"] is not None:
                if "odometer" not in data or data["odometer"] is None:
                    data["odometer"] = data["mileage_km"]
            elif "odometer" in data and data["odometer"] is not None:
                if "mileage_km" not in data or data["mileage_km"] is None:
                    data["mileage_km"] = data["odometer"]

            if "city" in data and data["city"]:
                meta = dict(data.get("metadata") or {})
                meta["city"] = data["city"]
                data["metadata"] = meta
        return data


class VehicleOut(VehicleBase):
    id: str
    user_id: str = "default_user"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

