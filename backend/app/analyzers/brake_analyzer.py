"""
AutoAssist AI - Brake System Safety & Wear Problem Analyzer
Calculates braking safety clearances, hydraulic integrity, rotor runout, and pad wear thresholds.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.app.analyzers.base import (
    ProblemAnalysisResult,
    DiagnosticCause,
    ActionStep,
    RiskLevel,
    CostEstimate,
    escalate_risk
)
from backend.app.analyzers.cost_estimator import get_cost_estimate
from backend.app.rag.retriever import AutomotiveRetriever


class BrakeAnalysisRequest(BaseModel):
    pad_thickness_mm: float = Field(..., ge=0.0, le=15.0, description="Minimum brake pad friction material in millimeters")
    pedal_feel: str = Field(
        default="normal_firm",
        description="'normal_firm', 'spongy_soft', 'sinks_to_floor', 'hard_high_effort', 'pulsating_vibrating'"
    )
    rotor_condition: Optional[str] = Field(
        default="smooth",
        description="'smooth', 'grooved_scored', 'warped_pulsating', 'excessive_rust_lip'"
    )
    pulls_when_braking: Optional[str] = Field(
        default="none",
        description="'none', 'pulls_left', 'pulls_right'"
    )
    abs_warning_light: bool = Field(default=False)
    brake_fluid_moisture_pct: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="DOT fluid moisture content %")
    include_rag_chunks: bool = True


class BrakeProblemAnalyzer:
    """Evaluates hydraulic braking integrity and friction wear specs according to DOT standards."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def analyze(self, request: BrakeAnalysisRequest) -> ProblemAnalysisResult:
        urgency = RiskLevel.LOW
        is_safe = True
        driving_advisory = "Braking performance is within safe factory specifications."
        repair_key = "brake_pads_rotors_replacement"

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        telemetry: Dict[str, Any] = {
            "pad_thickness_mm": request.pad_thickness_mm,
            "pedal_feel": request.pedal_feel,
            "rotor_condition": request.rotor_condition,
            "pulls_when_braking": request.pulls_when_braking,
            "abs_light": request.abs_warning_light
        }

        # 1. Pad Wear Evaluation
        if request.pad_thickness_mm <= 2.0:
            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "DANGER: Critical brake pad wear (≤2mm). High hazard of friction failure, rotor gouging, and brake fade. Replace immediately."
            causes.append(DiagnosticCause(
                title="Brake Pads at Absolute Rejection Limit (≤2mm)",
                probability=90,
                explanation="Friction material is nearly exhausted. Thermal bonding layer exposed to rotor.",
                common_indicators=["Metallic scraping, pad backing plate near rotor face"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Replace Front/Rear Brake Pads and Rotors",
                description="Install premium ceramic or semi-metallic pads. Measure rotor thickness with micrometer; replace if below discard specification.",
                tools_needed=["Brake caliper compressor tool", "Metric socket set", "Torque wrench"]
            ))
        elif request.pad_thickness_mm <= 3.5:
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Brake pads are approaching service limit (~3mm). Schedule service within 1,000 miles."
            causes.append(DiagnosticCause(
                title="Brake Pads Approaching Wear Limit",
                probability=60,
                explanation="Pads retain 15-25% service life. Acoustic wear indicators may begin chirping."
            ))
        else:
            telemetry["pad_life_status"] = f"HEALTHY ({request.pad_thickness_mm}mm remaining, ~{int((request.pad_thickness_mm/10.0)*100)}% pad life)"

        # 2. Pedal Feel Evaluation
        if request.pedal_feel == "sinks_to_floor":
            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "DO NOT DRIVE: Brake pedal sinking to floor indicates internal hydraulic fluid bypass in the Master Cylinder or major external leak. Braking failure imminent!"
            repair_key = "brake_master_cylinder"
            causes.insert(0, DiagnosticCause(
                title="Brake Master Cylinder Internal Cup Seal Leak (Pressure Bypass)",
                probability=85,
                explanation="Primary or secondary piston rubber cup seals have scored or collapsed, allowing hydraulic fluid to leak backwards into reservoir under steady pedal pressure.",
                common_indicators=["Pedal slowly drops to floorboard when held down at traffic lights"]
            ))
            steps.append(ActionStep(
                step_number=len(steps) + 1,
                title="Inspect Master Cylinder & Hydraulic Circuit",
                description="Check brake fluid reservoir level. If level is full but pedal sinks, master cylinder internal seals are bypassing.",
                tools_needed=["Inspection flashlight", "Flare nut wrenches"]
            ))
        elif request.pedal_feel == "spongy_soft":
            urgency = escalate_risk(urgency, RiskLevel.HIGH)
            driving_advisory = "Brake pedal is spongy. Air is compressible; stopping distances are dangerously elongated."
            causes.append(DiagnosticCause(
                title="Trapped Air in Hydraulic Brake Lines or Boiled Fluid",
                probability=70,
                explanation="Air bubbles compress under hydraulic pressure instead of transferring force to caliper pistons.",
                common_indicators=["Pedal can be 'pumped up' to become firm"]
            ))
            steps.append(ActionStep(
                step_number=len(steps) + 1,
                title="Perform Complete 4-Wheel Brake Bleeding",
                description="Bleed calipers in factory sequence (typically Passenger Rear, Driver Rear, Passenger Front, Driver Front) until clear, bubble-free fluid emerges.",
                tools_needed=["Bleeder bottle with check valve", "DOT 3 or DOT 4 brake fluid"]
            ))
        elif request.pedal_feel == "hard_high_effort":
            urgency = escalate_risk(urgency, RiskLevel.MEDIUM)
            driving_advisory = "Brake booster assist is inoperative. Requires very high leg effort to stop vehicle."
            causes.append(DiagnosticCause(
                title="Brake Vacuum Booster or Check Valve Failure",
                probability=80,
                explanation="Vacuum diaphragm ruptured or vacuum check valve from intake manifold stuck closed, removing power brake assist.",
                common_indicators=["Pedal feels like stepping on a solid brick"]
            ))

        # 3. Vibration / Rotor Pulsation
        if request.pedal_feel == "pulsating_vibrating" or request.rotor_condition == "warped_pulsating":
            causes.append(DiagnosticCause(
                title="Brake Rotor Thickness Variation (DTV) or Lateral Runout",
                probability=85,
                explanation="Excessive rotor lateral runout (>0.002 inch) or disc thickness variation creates high-frequency hydraulic kickback through pedal and steering shake.",
                common_indicators=["Steering wheel shakes back and forth while applying brakes at 50+ MPH"]
            ))

        # 4. Pulling to one side
        if request.pulls_when_braking in ["pulls_left", "pulls_right"]:
            repair_key = "brake_caliper_replacement"
            causes.append(DiagnosticCause(
                title="Sticking Brake Caliper Slide Pins or Seized Piston",
                probability=75,
                explanation=f"Caliper on opposite or pulling side has seized slide pins or rusty piston, creating uneven braking torque.",
                common_indicators=["Vehicle pulls toward the working caliper side during hard stops"]
            ))

        # 5. Moisture in fluid
        if request.brake_fluid_moisture_pct is not None:
            telemetry["fluid_moisture_pct"] = request.brake_fluid_moisture_pct
            if request.brake_fluid_moisture_pct > 3.0:
                urgency = escalate_risk(urgency, RiskLevel.HIGH)
                causes.append(DiagnosticCause(
                    title="Brake Fluid Water Contamination (>3% Moisture)",
                    probability=65,
                    explanation="DOT fluid is hygroscopic (absorbs moisture from air). Water drops boiling point from 401°F down to 284°F, causing sudden vapor-lock brake loss on steep downhill grades."
                ))

        if not causes:
            causes.append(DiagnosticCause(
                title="Brake Friction and Hydraulic Systems in Good Order",
                probability=100,
                explanation="Pad friction thickness, rotor surface, and pedal hydraulic feel meet manufacturer standards."
            ))

        total_p = sum(c.probability for c in causes)
        if total_p > 0:
            for c in causes:
                c.probability = int(round((c.probability / total_p) * 100))

        cost = get_cost_estimate(repair_key, fallback_title="Brake Service")

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                rag_resp = retriever.search(query=f"brake service {request.pedal_feel} pads rotors bleeding", top_k=2)
                for item in rag_resp.results:
                    rag_chunks.append({
                        "document_title": item.document_title,
                        "section": item.section,
                        "similarity": item.similarity,
                        "content": item.content[:350] + ("..." if len(item.content) > 350 else "")
                    })
            except Exception:
                pass

        return ProblemAnalysisResult(
            analyzer_id="brake_system_analyzer",
            analyzer_title="Brake System Safety & Wear Problem Analyzer",
            subsystem="Hydraulic Braking & Safety System",
            primary_verdict=f"Brake Assessment: {causes[0].title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
