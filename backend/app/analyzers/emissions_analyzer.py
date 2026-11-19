"""
AutoAssist AI - Fuel Trim, Economy & Emissions Problem Analyzer
Diagnoses fuel delivery, vacuum leaks, air metering (MAF/MAP), and exhaust gas anomalies.
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


class EmissionsAnalysisRequest(BaseModel):
    stft_idle_pct: float = Field(default=0.0, ge=-35.0, le=35.0, description="Short Term Fuel Trim at idle (-25% to +25%)")
    ltft_idle_pct: float = Field(default=0.0, ge=-35.0, le=35.0, description="Long Term Fuel Trim at idle (-25% to +25%)")
    stft_2500rpm_pct: Optional[float] = Field(default=None, ge=-35.0, le=35.0, description="STFT at 2,500 RPM")
    ltft_2500rpm_pct: Optional[float] = Field(default=None, ge=-35.0, le=35.0, description="LTFT at 2,500 RPM")
    mpg_drop_pct: Optional[float] = Field(default=None, ge=0.0, le=80.0, description="Drop in fuel efficiency %")
    exhaust_smoke_color: str = Field(default="none", description="'none', 'black_unburned_fuel', 'blue_burning_oil', 'white_sweet_coolant'")
    raw_fuel_odor: bool = Field(default=False)
    include_rag_chunks: bool = True


class EmissionsProblemAnalyzer:
    """Calculates stoichiometric fuel imbalances, vacuum leaks, and emissions component failures."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def analyze(self, request: EmissionsAnalysisRequest) -> ProblemAnalysisResult:
        total_trim_idle = request.stft_idle_pct + request.ltft_idle_pct
        urgency = RiskLevel.LOW
        is_safe = True
        driving_advisory = "Fuel metering and combustion stoichiometry are normal."
        repair_key = "vacuum_leak_repair"

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        telemetry: Dict[str, Any] = {
            "total_trim_idle_pct": round(total_trim_idle, 1),
            "stft_idle": request.stft_idle_pct,
            "ltft_idle": request.ltft_idle_pct,
            "exhaust_smoke": request.exhaust_smoke_color,
            "fuel_smell": request.raw_fuel_odor
        }

        # Case 1: Lean Mixture at Idle
        if total_trim_idle > 12.0:
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Engine running lean. If Total Trim exceeds +25%, DTC P0171 will set and engine may stumble or hesitate."

            # Check if 2500 RPM trim is provided
            if request.ltft_2500rpm_pct is not None:
                total_trim_2500 = (request.stft_2500rpm_pct or 0.0) + request.ltft_2500rpm_pct
                telemetry["total_trim_2500rpm_pct"] = round(total_trim_2500, 1)

                if total_trim_2500 < total_trim_idle - 8.0:
                    # Classic vacuum leak: large at idle, vanishes at high airflow
                    repair_key = "vacuum_leak_repair"
                    causes.append(DiagnosticCause(
                        title="Intake Manifold / PCV System Vacuum Leak",
                        probability=85,
                        explanation="Fuel trim is +{0:.1f}% at idle but normalizes to +{1:.1f}% at 2,500 RPM. This is the hallmark proof of unmetered air entering downstream of the throttle body.".format(total_trim_idle, total_trim_2500),
                        common_indicators=["Hissing sound under hood", "Rough idle that smooths out off-idle"]
                    ))
                    steps.append(ActionStep(
                        step_number=1,
                        title="Perform Intake Smoke Test",
                        description="Inject smoke into intake manifold while plugging throttle inlet. Look for smoke emerging from intake gasket or PCV hose.",
                        tools_needed=["Automotive smoke machine"]
                    ))
                else:
                    # High at both idle and 2500 RPM: fuel delivery or MAF issue
                    repair_key = "maf_sensor_clean_or_replace"
                    causes.append(DiagnosticCause(
                        title="Contaminated Mass Airflow (MAF) Sensor or Low Fuel Pressure",
                        probability=75,
                        explanation="Trim stays elevated (+{0:.1f}%) at both idle and 2500 RPM. Sensor wire is under-measuring incoming air volume across all RPM ranges.".format(total_trim_idle),
                        common_indicators=["Sluggish acceleration under highway load"]
                    ))
                    steps.append(ActionStep(
                        step_number=1,
                        title="Clean MAF Sensor Wire & Check Fuel Pressure",
                        description="Clean MAF sensor with aerosol MAF cleaner. Verify fuel rail pressure with mechanical gauge.",
                        tools_needed=["MAF cleaner spray", "Fuel pressure test gauge"]
                    ))
            else:
                causes.append(DiagnosticCause(
                    title="Lean Fuel Imbalance (Vacuum Leak or Under-Reporting MAF)",
                    probability=70,
                    explanation=f"ECM is adding +{total_trim_idle:.1f}% fuel correction to compensate for excess oxygen detected in exhaust."
                ))

        # Case 2: Rich Mixture at Idle (Subtracting fuel)
        elif total_trim_idle < -10.0:
            urgency = RiskLevel.MEDIUM
            repair_key = "oxygen_sensor_replacement"
            causes.append(DiagnosticCause(
                title="Leaking Fuel Injector or High Fuel Rail Pressure",
                probability=65,
                explanation=f"Total fuel trim is negative ({total_trim_idle:.1f}%). ECM is reducing fuel injection duration because too much fuel is present in combustion chamber.",
                common_indicators=["Strong gas smell from exhaust tailpipe", "Black carbon deposits on spark plugs"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Fuel Injector Leak-Down Residual Pressure Test",
                description="Key on to pressurize fuel rail, then key off. Rail pressure should hold steady for 15 minutes. If pressure drops quickly, an injector pintle is leaking.",
                tools_needed=["Fuel rail pressure gauge kit"]
            ))

        # Case 3: Exhaust Smoke Evaluation
        if request.exhaust_smoke_color == "black_unburned_fuel":
            urgency = escalate_risk(urgency, RiskLevel.MEDIUM)
            causes.insert(0, DiagnosticCause(
                title="Incomplete Fuel Combustion (Heavy Rich Running)",
                probability=80,
                explanation="Black tailpipe smoke consists of raw unburned soot particles. Catalytic converter will overheat and clog if neglected."
            ))
        elif request.exhaust_smoke_color == "blue_burning_oil":
            urgency = escalate_risk(urgency, RiskLevel.MEDIUM)
            causes.insert(0, DiagnosticCause(
                title="Engine Oil Burning (Valve Stem Seals or Piston Oil Rings)",
                probability=80,
                explanation="Oil leaking into combustion chambers creates distinctive blue-tinted exhaust haze and consumes engine oil.",
                common_indicators=["Puff of blue smoke after long downhill coasting or morning start"]
            ))
        elif request.exhaust_smoke_color == "white_sweet_coolant":
            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "Coolant burning inside engine cylinder! Risk of cylinder hydraulic lock and engine destruction."
            repair_key = "cylinder_head_gasket"
            causes.insert(0, DiagnosticCause(
                title="Coolant Leaking into Combustion Chamber (Head Gasket Breach)",
                probability=90,
                explanation="White exhaust smoke that smells sweet like pancake syrup is vaporized ethylene glycol."
            ))

        if not causes:
            causes.append(DiagnosticCause(
                title="Fuel Trim & Stoichiometric Air-Fuel Ratio Optimal",
                probability=100,
                explanation="Fuel trim is within ±5%, indicating optimal stoichiometric 14.7:1 air-fuel combustion."
            ))

        total_p = sum(c.probability for c in causes)
        if total_p > 0:
            for c in causes:
                c.probability = int(round((c.probability / total_p) * 100))

        cost = get_cost_estimate(repair_key, fallback_title="Emissions Service")

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                rag_resp = retriever.search(query=f"fuel trim vacuum leak MAF sensor emissions {request.exhaust_smoke_color}", top_k=2)
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
            analyzer_id="emissions_fuel_analyzer",
            analyzer_title="Fuel Trim, Economy & Emissions Problem Analyzer",
            subsystem="Fuel Delivery & Emissions Control",
            primary_verdict=f"Emissions Verdict: {causes[0].title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
