from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class SeverityRequest(BaseModel):
    symptom_or_code: Optional[str] = Field(None, description="Reported symptom, warning light, or failure description")
    query: Optional[str] = Field(None, description="Alias for symptom_or_code")
    subsystem: Optional[str] = Field("General", description="Automotive subsystem if known")
    can_vehicle_steer_and_stop: Optional[bool] = Field(True, description="Whether steering and brakes function normally")
    smoke_or_fire_detected: Optional[bool] = Field(False, description="Presence of active smoke, fire, or fuel smell")
    temperature_in_red: Optional[bool] = Field(False, description="Engine temperature gauge pegged in red danger zone")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("symptom_or_code") and data.get("query"):
                data["symptom_or_code"] = data["query"]
            if not data.get("symptom_or_code"):
                data["symptom_or_code"] = "General Vehicle Check"
        return data


class SeverityResponse(BaseModel):
    category: str  # "LOW", "MODERATE", "CRITICAL"
    badge_title: str
    is_safe_to_drive: bool
    urgency_level: str
    rationale: str
    warning_signs: List[str]
    immediate_action: str
    mechanic_visit_advice: str
    stop_driving_notice: Optional[str] = None
    severity: Optional[str] = None  # Alias for category

    @model_validator(mode="after")
    def set_severity_alias(self) -> "SeverityResponse":
        if not self.severity:
            self.severity = self.category
        return self

    disclaimer: str = (
        "The problem severity indicator is an informational assistance tool based on automotive engineering principles, "
        "not a certified physical safety inspection. If you feel unsafe operating your vehicle, pull over safely and seek professional assistance."
    )
