from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class RepairPricingItem(BaseModel):
    item_key: str
    part_name: str
    category: str
    compatible_makes: List[str] = ["Generic"]
    compatible_models: List[str] = ["All"]
    year_min: int = 2000
    year_max: int = 2026
    part_price_min: float
    part_price_max: float
    labor_hours_min: float
    labor_hours_max: float
    labor_rate_hourly: float = 600.0
    additional_expenses_estimate: float = 250.0
    difficulty: str = "Intermediate"
    city: str = "All India"
    currency: str = "INR"
    source: str = "OEM Standard Benchmarks"
    description: Optional[str] = None


class RepairEstimateRequest(BaseModel):
    issue_or_part: Optional[str] = Field(None, description="Reported problem, symptom, or spare part name")
    problem_query: Optional[str] = Field(None, description="Alias for issue_or_part")
    make: Optional[str] = Field("Generic", description="Vehicle manufacturer")
    vehicle_make: Optional[str] = Field(None, description="Alias for make")
    model: Optional[str] = Field("All", description="Vehicle model")
    vehicle_model: Optional[str] = Field(None, description="Alias for model")
    year: Optional[int] = Field(None, description="Manufacturing year")
    vehicle_year: Optional[int] = Field(None, description="Alias for year")
    fuel_type: Optional[str] = Field(None, description="Fuel type")
    city: Optional[str] = Field("All India", description="Location or city name")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("issue_or_part") and data.get("problem_query"):
                data["issue_or_part"] = data["problem_query"]
            if data.get("vehicle_make") and not data.get("make"):
                data["make"] = data["vehicle_make"]
            if data.get("vehicle_model") and not data.get("model"):
                data["model"] = data["vehicle_model"]
            if data.get("vehicle_year") and not data.get("year"):
                data["year"] = data["vehicle_year"]
            if not data.get("issue_or_part"):
                data["issue_or_part"] = "General Diagnostic"
        return data


class RepairEstimateResponse(BaseModel):
    query: str
    matched: bool
    part_name: str
    category: str
    vehicle_applied: str
    city_applied: str
    currency: str = "INR"
    parts_cost_range_inr: str
    parts_cost_min: float
    parts_cost_max: float
    labor_hours: float
    labor_charge_inr: str
    labor_charge_min: float
    labor_charge_max: float
    additional_expenses_inr: str
    additional_expenses: float
    total_estimated_cost_inr: str
    total_min: float
    total_max: float
    difficulty: str
    pricing_source: str
    disclaimer: str = (
        "This is an approximate repair cost estimate, not an official garage quotation. "
        "Actual costs may vary depending on vehicle condition, parts availability, location, "
        "and service-centre pricing."
    )
