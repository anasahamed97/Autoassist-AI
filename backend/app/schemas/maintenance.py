from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class MaintenanceRecordBase(BaseModel):
    vehicle_id: Optional[str] = None
    service_type: str = Field(..., description="Service type, e.g. Engine Oil & Filter Change")
    interval_months: int = Field(default=6, ge=1, description="Interval in months")
    interval_km: int = Field(default=10000, ge=500, description="Interval in kilometers")
    last_service_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    last_service_odometer: Optional[int] = Field(None, ge=0)
    current_odometer: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordOut(MaintenanceRecordBase):
    id: str
    user_id: str = "default_user"
    next_due_date: Optional[str] = None
    next_due_odometer: Optional[int] = None
    remaining_km: Optional[int] = None
    remaining_days: Optional[int] = None
    status: str = "upcoming"  # upcoming, due_soon, overdue, completed
    created_at: Optional[str] = None
    service_name: Optional[str] = None

    @model_validator(mode="after")
    def set_service_name_alias(self) -> "MaintenanceRecordOut":
        if not self.service_name:
            self.service_name = self.service_type
        return self


class MaintenanceOverview(BaseModel):
    total_records: int
    overdue_count: int
    due_soon_count: int
    upcoming_count: int
    records: List[MaintenanceRecordOut]
    items: Optional[List[MaintenanceRecordOut]] = None

    @model_validator(mode="after")
    def populate_items_alias(self) -> "MaintenanceOverview":
        if not self.items:
            self.items = self.records
        return self
