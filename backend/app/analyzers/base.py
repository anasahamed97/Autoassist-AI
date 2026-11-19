"""
AutoAssist AI - Problem Analyzers Base Schemas & Classes
Defines standardized data models for all automotive problem analyzers.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


RISK_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


def escalate_risk(r1: RiskLevel, r2: RiskLevel) -> RiskLevel:
    """Safely escalates risk level to whichever is higher in severity."""
    score1 = RISK_ORDER.get(r1, 1)
    score2 = RISK_ORDER.get(r2, 1)
    return r1 if score1 >= score2 else r2


class DifficultyLevel(str, Enum):
    BEGINNER = "Beginner (1/5)"
    INTERMEDIATE = "Intermediate DIY (2-3/5)"
    ADVANCED = "Advanced DIY (4/5)"
    PROFESSIONAL = "Professional Mechanic Only (5/5)"


class DiagnosticCause(BaseModel):
    title: str = Field(..., description="Probable root cause title")
    probability: int = Field(..., ge=0, le=100, description="Estimated likelihood percentage (0-100%)")
    explanation: str = Field(..., description="Technical rationale for this cause")
    common_indicators: List[str] = Field(default_factory=list, description="Associated symptoms or sensor readings")


class ActionStep(BaseModel):
    step_number: int
    title: str
    description: str
    tools_needed: List[str] = Field(default_factory=list)
    safety_warning: Optional[str] = None


class CostEstimate(BaseModel):
    diy_parts_cost_range_inr: str = "₹3,500 - ₹12,500"
    professional_labor_hours: float = 1.0
    professional_total_cost_range_inr: str = "₹8,500 - ₹22,000"
    diy_parts_cost_range_usd: str = "$40 - $150"
    professional_total_cost_range_usd: str = "$100 - $260"
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    recommended_action: str = "Inspect and test before replacing parts"


class ProblemAnalysisResult(BaseModel):
    analyzer_id: str = Field(..., description="Identifier of the analyzer that generated this report")
    analyzer_title: str = Field(..., description="Human-readable title of the analyzer")
    subsystem: str = Field(..., description="Automotive subsystem (e.g., Electrical, Cooling, Powertrain)")
    primary_verdict: str = Field(..., description="High-level diagnostic conclusion")
    urgency: RiskLevel = Field(default=RiskLevel.MEDIUM)
    is_safe_to_drive: bool = Field(default=True, description="Whether the vehicle can safely be driven in current condition")
    driving_advisory: str = Field(default="Drive cautiously to an inspection facility.")
    probable_causes: List[DiagnosticCause] = Field(default_factory=list)
    action_plan: List[ActionStep] = Field(default_factory=list)
    cost_estimate: Optional[CostEstimate] = None
    telemetry_summary: Dict[str, Any] = Field(default_factory=dict)
    rag_reference_chunks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Matched technical service manual chunks from RAG vector store"
    )
    safety_disclaimer: str = (
        "Automated diagnostic analysis provided for technical assistance. "
        "Always adhere to factory service manual safety protocols and verify with professional diagnostic equipment."
    )
