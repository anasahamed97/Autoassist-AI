from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class QuoteItemInput(BaseModel):
    service_or_part: Optional[str] = Field(None, description="Name of repair, service or part quoted by mechanic")
    item_name: Optional[str] = Field(None, description="Alias for service_or_part")
    quantity: int = Field(default=1, ge=1, description="Quantity of parts")
    quoted_part_price: float = Field(default=0.0, ge=0.0, description="Quoted unit or total part price in INR")
    quoted_labor_price: float = Field(default=0.0, ge=0.0, description="Quoted labor charges in INR")
    quoted_additional: float = Field(default=0.0, ge=0.0, description="Any consumables, taxes, or extra fees in INR")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("service_or_part") and data.get("item_name"):
                data["service_or_part"] = data["item_name"]
            if not data.get("service_or_part"):
                data["service_or_part"] = "General Repair Service"
        return data


class QuoteComparisonRequest(BaseModel):
    repair_title: Optional[str] = Field("Mechanic Quotation Review", description="Overall quotation title or symptom")
    title: Optional[str] = Field(None, description="Alias for repair_title")
    garage_name: Optional[str] = Field(None, description="Name of service centre or garage")
    make: Optional[str] = Field("Generic", description="Vehicle manufacturer")
    model: Optional[str] = Field("All", description="Vehicle model")
    city: Optional[str] = Field("All India", description="City for labor rates")
    items: List[QuoteItemInput] = Field(..., min_length=1, description="Line items quoted by mechanic")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("repair_title") and data.get("title"):
                data["repair_title"] = data["title"]
        return data


class QuoteItemResult(BaseModel):
    service_or_part: str
    quantity: int
    quoted_part_price: float
    quoted_labor_price: float
    quoted_additional: float
    quoted_total: float
    reference_found: bool
    reference_part_min: float
    reference_part_max: float
    reference_labor_min: float
    reference_labor_max: float
    reference_total_min: float
    reference_total_max: float
    reference_range_display: str
    difference_min: float
    difference_max: float
    status: str  # "Within reference range", "Above reference range", "Below reference range", "Insufficient pricing data"
    status_color: str  # "green", "amber", "blue", "gray"
    notes: str


class QuoteComparisonResponse(BaseModel):
    repair_title: str
    garage_name: Optional[str]
    total_quoted: float
    total_reference_min: float
    total_reference_max: float
    overall_status: str
    difference_summary: str
    items: List[QuoteItemResult]
    educational_note: str = (
        "Important Note: A quotation higher than the reference range does NOT automatically mean overcharging. "
        "Original Equipment Manufacturer (OEM) genuine parts, premium warranty, dealer infrastructure, and "
        "certified technician expertise can justify higher prices. Use these benchmarks to discuss details with your mechanic."
    )
    suggested_mechanic_questions: List[str]
