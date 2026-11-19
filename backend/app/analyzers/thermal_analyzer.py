"""
AutoAssist AI - Engine Cooling & Thermal Overheating Problem Analyzer
Pinpoints root causes of engine overheating based on thermal conditions and symptom triggers.
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


class ThermalAnalysisRequest(BaseModel):
    driving_condition: str = Field(
        ...,
        description="Condition when overheating occurs: 'idle_traffic', 'highway_speed', 'all_times_rapid', 'climbing_hills', 'erratic_spikes'"
    )
    coolant_level: str = Field(
        default="normal",
        description="'normal', 'low_with_visible_puddle', 'low_no_puddle', 'empty'"
    )
    electric_fan_running: Optional[str] = Field(
        default="unknown",
        description="'yes_high_speed', 'no_not_spinning', 'unknown'"
    )
    cabin_heater_output: Optional[str] = Field(
        default="hot",
        description="'hot', 'lukewarm_or_cold', 'unknown'"
    )
    hose_temperature_differential: Optional[str] = Field(
        default="unknown",
        description="'both_hot', 'upper_scalding_lower_cold', 'both_lukewarm', 'unknown'"
    )
    white_exhaust_smoke_or_milky_oil: bool = Field(
        default=False,
        description="Presence of sweet white exhaust smoke or milkshake emulsion under oil cap"
    )
    include_rag_chunks: bool = True


class ThermalProblemAnalyzer:
    """Diagnoses engine cooling failures and overheating mechanisms."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def analyze(self, request: ThermalAnalysisRequest) -> ProblemAnalysisResult:
        urgency = RiskLevel.CRITICAL
        is_safe = False
        driving_advisory = (
            "DO NOT DRIVE the vehicle while temperature gauge is in the red zone! "
            "Aluminum cylinder heads warp within 3 to 5 minutes of severe overheating, leading to catastrophic engine replacement ($4,000+)."
        )
        repair_key = "thermostat_replacement"

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        telemetry: Dict[str, Any] = {
            "condition": request.driving_condition,
            "coolant_level": request.coolant_level,
            "cabin_heater": request.cabin_heater_output,
            "hose_temp": request.hose_temperature_differential,
        }

        # Priority 1: Blown Cylinder Head Gasket
        if request.white_exhaust_smoke_or_milky_oil or request.coolant_level == "low_no_puddle":
            repair_key = "cylinder_head_gasket"
            causes.append(DiagnosticCause(
                title="Blown Cylinder Head Gasket (Combustion Breach)",
                probability=75,
                explanation="Combustion gases entering cooling passages displace liquid coolant, causing steam pockets and severe overheating.",
                common_indicators=["Milky froth on oil dipstick", "Sweet smelling white exhaust smoke", "Rapid violent bubbling in radiator neck"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Perform Combustion Gas Block Test (Block Check)",
                description="Place a combustion leak test tube with blue bromothymol blue reagent fluid onto the radiator neck. If fluid turns yellow/green, exhaust hydrocarbons are present.",
                tools_needed=["Block leak test kit with detector fluid"]
            ))

        # Priority 2: Stuck Closed Thermostat
        if request.hose_temperature_differential == "upper_scalding_lower_cold" or request.driving_condition == "all_times_rapid":
            repair_key = "thermostat_replacement"
            causes.append(DiagnosticCause(
                title="Thermostat Stuck in Closed Position",
                probability=70,
                explanation="The wax pellet valve failed to open at 195°F. Coolant inside the engine block cannot circulate to the radiator to dissipate heat.",
                common_indicators=["Upper radiator hose scalding hot while lower hose remains cold", "Overheating within 5-10 minutes of starting"]
            ))
            steps.append(ActionStep(
                step_number=len(steps) + 1,
                title="Inspect and Replace Thermostat",
                description="Allow engine to cool completely. Unbolt thermostat housing, inspect spring mechanism for binding, and install new OEM temperature-rated thermostat.",
                tools_needed=["10mm/12mm ratchet", "Coolant drain pan", "Fresh 50/50 coolant"]
            ))

        # Priority 3: Electric Cooling Fan Inoperative (Idle / Traffic Overheat)
        if request.driving_condition == "idle_traffic" or request.electric_fan_running == "no_not_spinning":
            repair_key = "cooling_fan_motor_relay"
            causes.append(DiagnosticCause(
                title="Electric Radiator Cooling Fan Motor or Relay Failure",
                probability=65,
                explanation="At standstill or low speeds, no ram-air passes through the radiator fins. The electric fan must pull air; without it, coolant temperature rises rapidly.",
                common_indicators=["Overheats at stoplights or drive-thrus, but cools down when cruising at 50 MPH"]
            ))
            steps.append(ActionStep(
                step_number=len(steps) + 1,
                title="Test Cooling Fan Relay and Motor with 12V Jumper",
                description="Turn on vehicle A/C to MAX; both radiator fans should immediately engage. If not, swap cooling fan relay with horn relay in under-hood fuse box.",
                tools_needed=["Multimeter or 12V test light", "Needle nose pliers"]
            ))

        # Priority 4: Water Pump Impeller Failure or Trapped Airlock
        if request.cabin_heater_output == "lukewarm_or_cold" and request.driving_condition in ["highway_speed", "all_times_rapid"]:
            repair_key = "water_pump_replacement"
            causes.append(DiagnosticCause(
                title="Water Pump Impeller Slippage / Separation or Airlock",
                probability=60,
                explanation="Plastic or stamped impellers can crack and spin free on the shaft. Coolant cannot circulate, starving the cabin heater core of hot fluid.",
                common_indicators=["Cabin heater blows ice-cold while temperature gauge is pegged in the red zone"]
            ))
            steps.append(ActionStep(
                step_number=len(steps) + 1,
                title="Inspect Water Pump Pulley and Serpentine Belt Drive",
                description="Check water pump shaft for wobble, bearing play, or coolant dripping from the weep hole.",
                tools_needed=["Flashlight", "Inspection mirror"]
            ))

        # Priority 5: Radiator Clogging (Highway Speed Overheating)
        if request.driving_condition == "highway_speed" and not causes:
            repair_key = "radiator_replacement"
            causes.append(DiagnosticCause(
                title="Internal Radiator Core Mineral Clogging or External Fin Blockage",
                probability=55,
                explanation="At highway speeds the engine generates peak heat (BTUs). A clogged radiator cannot achieve necessary heat transfer flow rate.",
                common_indicators=["Temperature rises as speed increases, cools down when coasting"]
            ))

        # Default fallback
        if not causes:
            causes.append(DiagnosticCause(
                title="Cooling System Low Pressure / Faulty Radiator Cap",
                probability=45,
                explanation="Weak spring in radiator pressure cap drops boiling point from 265°F to 212°F, causing premature boilover into reservoir tank."
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Pressure Test Radiator and Cap",
                description="Attach hand pressure tester to radiator neck. Pump to 16 PSI and check for pressure loss over 2 minutes.",
                tools_needed=["Cooling system pressure tester kit"]
            ))

        # Normalize probabilities
        total_p = sum(c.probability for c in causes)
        if total_p > 0:
            for c in causes:
                c.probability = int(round((c.probability / total_p) * 100))

        cost = get_cost_estimate(repair_key, fallback_title="Cooling System Repair")

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                rag_resp = retriever.search(query=f"engine overheating cooling system {request.driving_condition} thermostat water pump", top_k=2)
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
            analyzer_id="thermal_cooling_analyzer",
            analyzer_title="Engine Overheating & Cooling System Problem Analyzer",
            subsystem="Engine Cooling & Thermal Management",
            primary_verdict=f"Thermal Diagnosis: {causes[0].title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
