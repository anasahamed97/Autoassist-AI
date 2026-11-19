"""
AutoAssist AI - Starting & Charging System Multimeter Analyzer
Calculates Battery State of Charge, Alternator Output Health, Starter Voltage Drop, and Parasitic Drain.
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


class ElectricalAnalysisRequest(BaseModel):
    resting_voltage: float = Field(..., ge=6.0, le=18.0, description="Resting battery voltage with engine OFF (e.g. 12.6V)")
    cranking_voltage: Optional[float] = Field(None, ge=4.0, le=15.0, description="Minimum voltage during engine crank (e.g. 10.2V)")
    alternator_running_voltage: Optional[float] = Field(None, ge=8.0, le=20.0, description="Voltage with engine idling and loads ON (e.g. 14.2V)")
    parasitic_draw_ma: Optional[float] = Field(None, ge=0.0, le=5000.0, description="Key-off parasitic current in milliamps (e.g. 35 mA)")
    battery_age_years: Optional[float] = Field(None, ge=0.0, le=15.0, description="Age of battery in years")
    include_rag_chunks: bool = True


class ElectricalProblemAnalyzer:
    """Evaluates 12V automotive electrical health using standard SAE multimeter specifications."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    @staticmethod
    def calculate_soc_pct(voltage: float) -> int:
        """Estimates State of Charge % for standard 12V flooded/AGM lead-acid battery."""
        if voltage >= 12.66:
            return 100
        elif voltage >= 12.45:
            return int(75 + (voltage - 12.45) / (12.66 - 12.45) * 25)
        elif voltage >= 12.24:
            return int(50 + (voltage - 12.24) / (12.45 - 12.24) * 25)
        elif voltage >= 12.06:
            return int(25 + (voltage - 12.06) / (12.24 - 12.06) * 25)
        elif voltage >= 11.90:
            return int((voltage - 11.90) / (12.06 - 11.90) * 25)
        else:
            return 0

    def analyze(self, request: ElectricalAnalysisRequest) -> ProblemAnalysisResult:
        soc_pct = self.calculate_soc_pct(request.resting_voltage)
        urgency = RiskLevel.LOW
        is_safe = True
        driving_advisory = "Starting and charging systems are within operational specifications."
        repair_key = "battery_replacement"

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        telemetry: Dict[str, Any] = {
            "resting_voltage_v": request.resting_voltage,
            "calculated_state_of_charge_pct": soc_pct,
        }

        # 1. Evaluate Battery Resting Voltage
        if request.resting_voltage < 11.90:
            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "Battery is completely discharged or has a dead internal cell (<11.9V). Vehicle will not crank reliably."
            causes.append(DiagnosticCause(
                title="Deeply Discharged Battery or Shorted Internal Cell",
                probability=55,
                explanation=f"Resting voltage of {request.resting_voltage}V indicates 0% state of charge. Sulfation or cell short present."
            ))
        elif request.resting_voltage < 12.40:
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Battery state of charge is low (<75%). Recharge battery and test for parasitic draw."
            causes.append(DiagnosticCause(
                title="Undercharged 12V Battery",
                probability=40,
                explanation=f"Resting voltage of {request.resting_voltage}V reflects ~{soc_pct}% charge. Frequent short trips or key-off drain suspected."
            ))

        # 2. Evaluate Cranking Voltage
        if request.cranking_voltage is not None:
            telemetry["cranking_voltage_v"] = request.cranking_voltage
            if request.cranking_voltage < 9.6:
                urgency = escalate_risk(urgency, RiskLevel.HIGH)
                is_safe = False
                driving_advisory = "Excessive cranking voltage drop (<9.6V). High risk of no-start in cold weather."
                causes.append(DiagnosticCause(
                    title="Excessive Starter Voltage Drop / High Resistance Cables",
                    probability=45,
                    explanation=f"Cranking voltage dropped to {request.cranking_voltage}V (SAE threshold is 9.6V). Corroded terminals, worn starter motor, or depleted battery."
                ))
                steps.append(ActionStep(
                    step_number=1,
                    title="Perform Voltage Drop Test Across Battery Terminals",
                    description="Place multimeter probes between battery post and cable clamp during cranking. Drop should be <0.1V. If higher, clean terminal corrosion.",
                    tools_needed=["Digital Multimeter with Min/Max hold", "Wire terminal cleaner"]
                ))
            else:
                telemetry["starter_health"] = "EXCELLENT (Maintained >9.6V during crank)"

        # 3. Evaluate Alternator Running Voltage
        if request.alternator_running_voltage is not None:
            telemetry["alternator_running_voltage_v"] = request.alternator_running_voltage
            if request.alternator_running_voltage < 13.5:
                urgency = RiskLevel.CRITICAL
                is_safe = False
                driving_advisory = "Alternator is undercharging (<13.5V). The vehicle is running on reserve battery power and will stall when battery dies."
                repair_key = "alternator_replacement"
                causes.append(DiagnosticCause(
                    title="Alternator Undercharging / Faulty Voltage Regulator",
                    probability=65,
                    explanation=f"At {request.alternator_running_voltage}V, the alternator cannot sustain vehicle electrical loads and recharge battery simultaneously."
                ))
                steps.append(ActionStep(
                    step_number=len(steps) + 1,
                    title="Inspect Serpentine Belt & Alternator B+ Output",
                    description="Check serpentine drive belt for slippage or oil contamination. Measure DC voltage directly at alternator B+ terminal to verify output.",
                    tools_needed=["Digital multimeter", "Flashlight"]
                ))
            elif request.alternator_running_voltage > 15.0:
                urgency = RiskLevel.CRITICAL
                is_safe = False
                driving_advisory = "DANGER: Alternator is OVERCHARGING (>15.0V). Internal regulator has failed open, which can boil battery electrolyte and burn out vehicle computers (ECUs)."
                repair_key = "alternator_replacement"
                causes.append(DiagnosticCause(
                    title="Failed Internal Voltage Regulator (Overcharging)",
                    probability=85,
                    explanation=f"Alternator voltage of {request.alternator_running_voltage}V exceeds safe ceiling (14.8V). Extreme hazard of blown fuses, bulb burnout, and ECU damage."
                ))
            else:
                telemetry["alternator_health"] = "HEALTHY (Regulating within 13.8V - 14.6V)"

        # 4. Evaluate Parasitic Key-Off Draw
        if request.parasitic_draw_ma is not None:
            telemetry["parasitic_draw_ma"] = request.parasitic_draw_ma
            if request.parasitic_draw_ma > 80.0:
                urgency = escalate_risk(urgency, RiskLevel.MEDIUM)
                repair_key = "parasitic_draw_repair"
                causes.append(DiagnosticCause(
                    title="Excessive Parasitic Battery Drain",
                    probability=50,
                    explanation=f"Key-off drain of {request.parasitic_draw_ma} mA exceeds normal 50 mA limit. Will deplete a fully charged battery in 2 to 4 days."
                ))
                steps.append(ActionStep(
                    step_number=len(steps) + 1,
                    title="Fuse-Pulling Parasitic Drain Isolation Procedure",
                    description="Connect multimeter in series with negative battery cable on 10A DC current scale. Allow car modules to sleep for 20 minutes. Pull fuses one-by-one until current drops below 50mA.",
                    tools_needed=["Multimeter with fused 10A DC jack", "Fuse puller", "Under-dash fuse box diagram"]
                ))
            else:
                telemetry["parasitic_drain_health"] = "NORMAL (<50 mA key-off standby current)"

        # If all healthy
        if not causes:
            causes.append(DiagnosticCause(
                title="All Electrical Voltages Within Factory Tolerances",
                probability=100,
                explanation="Resting battery, cranking reserve, and alternator charging regulation meet SAE standards."
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Routine Battery Preventative Maintenance",
                description="Apply dielectric silicone grease or anti-corrosion spray to battery posts to prevent acid sulfation.",
                tools_needed=["Terminal protector spray"]
            ))

        # Age consideration
        if request.battery_age_years is not None and request.battery_age_years >= 4.0:
            telemetry["battery_age_note"] = f"Battery is {request.battery_age_years} years old (average lead-acid lifespan is 3-5 years)."

        cost = get_cost_estimate(repair_key, fallback_title="Electrical Charging Repair")

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                rag_resp = retriever.search(query="starting charging system battery alternator voltage drop parasitic draw", top_k=2)
                for item in rag_resp.results:
                    rag_chunks.append({
                        "document_title": item.document_title,
                        "section": item.section,
                        "similarity": item.similarity,
                        "content": item.content[:350] + ("..." if len(item.content) > 350 else "")
                    })
            except Exception:
                pass

        verdict = (
            f"Battery SoC: {soc_pct}% ({request.resting_voltage}V) | "
            f"Status: {'CRITICAL DEFECT' if urgency == RiskLevel.CRITICAL else 'ATTENTION REQUIRED' if urgency == RiskLevel.HIGH else 'ACCEPTABLE'}"
        )

        return ProblemAnalysisResult(
            analyzer_id="electrical_multimeter_analyzer",
            analyzer_title="Starting & Charging System Multimeter Analyzer",
            subsystem="Starting, Charging & 12V Electrical",
            primary_verdict=verdict,
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
