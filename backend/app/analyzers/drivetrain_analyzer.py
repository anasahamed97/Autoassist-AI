"""
AutoAssist AI - Transmission & Drivetrain Problem Analyzer
Diagnoses automatic transmissions, CVTs, manuals, torque converters, and fluid degradation states.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.app.analyzers.base import (
    ProblemAnalysisResult,
    DiagnosticCause,
    ActionStep,
    RiskLevel,
    CostEstimate
)
from backend.app.analyzers.cost_estimator import get_cost_estimate
from backend.app.rag.retriever import AutomotiveRetriever


class DrivetrainAnalysisRequest(BaseModel):
    transmission_type: str = Field(
        ...,
        description="'automatic_torque_converter', 'cvt_continuously_variable', 'manual_clutch', 'dual_clutch_dct'"
    )
    symptom: str = Field(
        ...,
        description="'slipping_rpm_flares', 'harsh_shift_jerk', 'delayed_drive_reverse', 'shudder_at_cruising_speed', 'grinding_into_gear', 'whine_in_all_gears'"
    )
    fluid_color: Optional[str] = Field(
        default="cherry_red_clean",
        description="'cherry_red_clean', 'translucent_brown', 'dark_burnt_black', 'milky_strawberry_shake', 'unknown'"
    )
    fluid_level: Optional[str] = Field(default="normal", description="'normal', 'low', 'overfilled', 'unknown'")
    include_rag_chunks: bool = True


class DrivetrainProblemAnalyzer:
    """Evaluates automatic, CVT, and manual drivetrain mechanical and hydraulic health."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def analyze(self, request: DrivetrainAnalysisRequest) -> ProblemAnalysisResult:
        urgency = RiskLevel.MEDIUM
        is_safe = True
        driving_advisory = "Drive gently without heavy acceleration; service drivetrain promptly."
        repair_key = "transmission_fluid_service"

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        telemetry: Dict[str, Any] = {
            "transmission_type": request.transmission_type,
            "symptom": request.symptom,
            "fluid_color": request.fluid_color,
            "fluid_level": request.fluid_level
        }

        # Priority 1: Coolant breach into transmission (Strawberry Milkshake of Death)
        if request.fluid_color == "milky_strawberry_shake":
            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "EMERGENCY: Coolant in transmission! Engine radiator internal trans cooler ruptured. Antifreeze destroys paper friction clutch linings and causes internal corrosion. Do not drive."
            repair_key = "radiator_replacement"
            causes.append(DiagnosticCause(
                title="Transmission Radiator Heat Exchanger Breach (Coolant Contamination)",
                probability=95,
                explanation="Engine coolant mixed with transmission fluid, creating an emulsion that delaminates clutch friction plates and swells seals.",
                common_indicators=["Pink frothy milky fluid on dipstick", "Transmission slipping and shuddering"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Replace Engine Radiator and Flush Transmission Lines",
                description="Install a new radiator or dedicated external transmission cooler. Transmission will require full disassembly and new clutch packs.",
                tools_needed=["Hose clamp pliers", "Transmission fluid flush machine"]
            ))

        # Priority 2: Burnt pitch black fluid with slipping
        elif request.fluid_color == "dark_burnt_black" or (request.symptom == "slipping_rpm_flares" and request.fluid_level == "normal"):
            urgency = RiskLevel.HIGH
            is_safe = False
            driving_advisory = "Severe transmission friction plate burnout. Continuing to drive will cause total loss of forward and reverse propulsion."
            repair_key = "transmission_fluid_service"
            causes.append(DiagnosticCause(
                title="Worn / Burned Internal Friction Clutch Packs or CVT Belt Slippage",
                probability=80,
                explanation="Clutch friction material has completely worn off steel plates, allowing planetary carriers or CVT pulleys to slip under engine torque.",
                common_indicators=["Engine revs flare between 2nd and 3rd gear", "Acrid burnt fluid odor"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Check Transmission Line Pressure & Drop Pan",
                description="Hook hydraulic gauge to transmission pressure test port. Drop pan and inspect bottom for metal shavings and friction silt.",
                tools_needed=["0-300 PSI hydraulic pressure gauge", "Pan drain socket", "Fluid catch pan"]
            ))

        # Priority 3: Shudder at cruising speed (Torque Converter Clutch Shudder)
        elif request.symptom == "shudder_at_cruising_speed":
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Drive with O/D off or tap brake lightly to disengage lockup. Safe for short commutes."
            causes.append(DiagnosticCause(
                title="Torque Converter Lockup Clutch Shudder (Degraded Friction Modifiers)",
                probability=75,
                explanation="At 35-50 MPH, the torque converter clutch slips and grabs intermittently because ATF friction modifiers have broken down.",
                common_indicators=["Rumble-strip vibration under gentle cruising throttle"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Perform Complete Transmission Fluid Flush & OEM Fluid Refill",
                description="Drain old fluid and refill with genuine OEM manufacturer specified synthetic fluid containing fresh anti-shudder friction modifiers.",
                tools_needed=["Fluid transfer pump", "OEM synthetic ATF fluid"]
            ))

        # Priority 4: Low fluid causing slipping
        elif request.fluid_level == "low" and request.symptom == "slipping_rpm_flares":
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Add approved transmission fluid before driving to prevent hydraulic pump cavitation."
            causes.append(DiagnosticCause(
                title="Low Transmission Fluid Level (Hydraulic Starvation)",
                probability=85,
                explanation="Fluid pump is drawing air pockets, causing mainline pressure to collapse below the 70 PSI required to clamp clutches.",
                common_indicators=["Slipping when turning corners or cold morning starts"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Top up Fluid to Hot Full Mark and Inspect for Leaks",
                description="Check transmission cooler lines, output shaft seals, and pan gasket for fluid seepage.",
                tools_needed=["Funnel with long tube", "OEM ATF fluid"]
            ))

        # Priority 5: Harsh engagement / shift clunk
        elif request.symptom == "harsh_shift_jerk":
            causes.append(DiagnosticCause(
                title="Defective Electronic Pressure Control (EPC) Solenoid or Broken Engine Mount",
                probability=65,
                explanation="High uncontrolled line pressure slams clutches together, or collapsed engine/transmission mount allows powertrain to pitch violently.",
                common_indicators=["Loud bang when shifting from Park to Reverse or Drive"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Power-Brake Engine Roll Inspection",
                description="Have helper hold brake and rev slightly in Drive; if engine tilts more than 1.5 inches, motor/trans mount is torn.",
                tools_needed=["Safety wheel chocks"]
            ))

        if not causes:
            causes.append(DiagnosticCause(
                title="Transmission Fluid & Shifting Behavior Stable",
                probability=100,
                explanation="Fluid color and hydraulic engagement meet expected parameters."
            ))

        total_p = sum(c.probability for c in causes)
        if total_p > 0:
            for c in causes:
                c.probability = int(round((c.probability / total_p) * 100))

        cost = get_cost_estimate(repair_key, fallback_title="Transmission Repair")

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                rag_resp = retriever.search(query=f"transmission drivetrain {request.transmission_type} {request.symptom} {request.fluid_color}", top_k=2)
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
            analyzer_id="drivetrain_transmission_analyzer",
            analyzer_title="Transmission & Drivetrain Health Problem Analyzer",
            subsystem="Transmission & Driveline",
            primary_verdict=f"Drivetrain Verdict: {causes[0].title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
