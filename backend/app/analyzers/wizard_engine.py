"""
AutoAssist AI - Multi-Step Interactive Diagnostic Wizard Engine
Provides guided question-and-answer symptom resolution with probability convergence.
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


class WizardOption(BaseModel):
    id: str
    label: str
    hint: Optional[str] = None


class WizardQuestion(BaseModel):
    id: str
    prompt: str
    options: List[WizardOption]


class WizardStartRequest(BaseModel):
    domain: str = Field(
        ...,
        description="'no_start', 'overheating', 'abnormal_noise', 'braking_issues', 'check_engine_light', 'transmission_slipping'"
    )


class WizardStepRequest(BaseModel):
    domain: str
    answers: Dict[str, str] = Field(default_factory=dict, description="Map of question_id -> option_id")
    include_rag_chunks: bool = True


WIZARD_DOMAINS: Dict[str, Dict[str, Any]] = {
    "no_start": {
        "title": "Starting Failure & Cranking Diagnostic Tree",
        "subsystem": "Starting & Ignition System",
        "questions": [
            WizardQuestion(
                id="crank_behavior",
                prompt="What happens when you turn the key or press the start button?",
                options=[
                    WizardOption(id="rapid_clicking", label="Rapid, sharp clicking sounds (chatter)", hint="Starter solenoid cycling on low voltage"),
                    WizardOption(id="single_click_silence", label="A single solid 'click' then complete silence", hint="Starter motor locked or solenoid contacts burnt"),
                    WizardOption(id="complete_silence", label="Absolute silence (no sound, dash lights may stay off)", hint="Dead battery, blown main fuse, or neutral safety switch"),
                    WizardOption(id="slow_crank", label="Crank is very slow, sluggish and groaning", hint="Weak battery or heavy cable resistance"),
                    WizardOption(id="cranks_normal_no_start", label="Engine cranks vigorously and fast, but will not catch and run", hint="Fuel delivery, ignition spark, or timing problem")
                ]
            ),
            WizardQuestion(
                id="headlights_test",
                prompt="Turn on your headlights. How do they behave?",
                options=[
                    WizardOption(id="bright_normal", label="Headlights are full brightness"),
                    WizardOption(id="very_dim", label="Headlights are very dim or yellowish"),
                    WizardOption(id="turn_off_when_cranking", label="Headlights go completely dark when turning key to start")
                ]
            ),
            WizardQuestion(
                id="fuel_gauge_odor",
                prompt="Is there gas in the tank and do you hear the fuel pump hum for 2 seconds when turning key to ON?",
                options=[
                    WizardOption(id="pump_hums_fuel_full", label="Yes, heard fuel pump hum and tank has fuel"),
                    WizardOption(id="no_pump_hum", label="No sound from rear fuel tank when turning key to ON"),
                    WizardOption(id="tank_near_empty", label="Fuel gauge is on Empty or low fuel light on")
                ]
            )
        ]
    },
    "overheating": {
        "title": "Engine Thermal & Overheating Diagnostic Tree",
        "subsystem": "Cooling System",
        "questions": [
            WizardQuestion(
                id="driving_scenario",
                prompt="Under what driving conditions does the temperature gauge rise?",
                options=[
                    WizardOption(id="idle_traffic", label="At idle, stoplights, or heavy slow traffic", hint="Electric fan or radiator airflow"),
                    WizardOption(id="highway_speed", label="Cruising at 55-70 MPH on highway", hint="Clogged radiator tubes or water pump"),
                    WizardOption(id="immediate_rapid", label="Rises within 5 minutes of starting engine", hint="Thermostat stuck closed or no coolant"),
                    WizardOption(id="climbing_hills", label="Only when climbing steep grades or towing")
                ]
            ),
            WizardQuestion(
                id="heater_test",
                prompt="Turn the cabin interior heater to MAX heat. What comes out of the vents?",
                options=[
                    WizardOption(id="heater_hot", label="Hot air blows out normally"),
                    WizardOption(id="heater_cold", label="Cold or lukewarm air blows out", hint="Indicates no coolant circulation to heater core!")
                ]
            ),
            WizardQuestion(
                id="puddle_or_smoke",
                prompt="Do you notice coolant puddles under the car or white sweet exhaust smoke?",
                options=[
                    WizardOption(id="green_puddle", label="Bright green/orange sweet puddle under front of car"),
                    WizardOption(id="white_exhaust_smoke", label="Puffy white exhaust smoke smelling like sweet syrup"),
                    WizardOption(id="no_puddle_smoke", label="No puddles and normal exhaust")
                ]
            )
        ]
    },
    "abnormal_noise": {
        "title": "Acoustic Noise & Mechanical Vibration Tree",
        "subsystem": "NVH & Chassis Mechanical",
        "questions": [
            WizardQuestion(
                id="noise_type",
                prompt="What does the sound most closely resemble?",
                options=[
                    WizardOption(id="squeal_screech", label="High-pitched squeal or screech", hint="Belts or brake wear indicators"),
                    WizardOption(id="metallic_grinding", label="Heavy metallic grinding or scraping", hint="Brake backing plates or wheel bearings"),
                    WizardOption(id="rhythmic_clicking", label="Fast clicking when turning sharp corners", hint="CV axle half-shaft"),
                    WizardOption(id="deep_knocking", label="Heavy deep knocking from inside engine", hint="Rod bearing or piston"),
                    WizardOption(id="clunking_bumps", label="Dull clunking when driving over potholes", hint="Sway bar links or suspension bushings")
                ]
            ),
            WizardQuestion(
                id="noise_timing",
                prompt="When is the sound loudest or most noticeable?",
                options=[
                    WizardOption(id="only_braking", label="Only when pressing the brake pedal"),
                    WizardOption(id="sharp_turns", label="Accelerating through sharp turns"),
                    WizardOption(id="speed_proportional", label="Gets louder as vehicle speed increases"),
                    WizardOption(id="rpm_proportional", label="Speeds up as engine is revved in park")
                ]
            )
        ]
    },
    "braking_issues": {
        "title": "Braking System & Hydraulic Safety Tree",
        "subsystem": "Brake System",
        "questions": [
            WizardQuestion(
                id="pedal_behavior",
                prompt="How does the brake pedal feel under your foot?",
                options=[
                    WizardOption(id="pedal_spongy", label="Spongy and soft, requires pumping to stop"),
                    WizardOption(id="pedal_sinks", label="Slowly sinks all the way to floor at traffic lights"),
                    WizardOption(id="pedal_pulsates", label="Pulsates and vibrates rapidly under heavy braking"),
                    WizardOption(id="pedal_hard", label="Rock-hard pedal, vehicle takes great effort to stop")
                ]
            ),
            WizardQuestion(
                id="vehicle_direction",
                prompt="Does the vehicle pull to one side when you brake firmly on a flat road?",
                options=[
                    WizardOption(id="tracks_straight", label="Car continues completely straight"),
                    WizardOption(id="pulls_sharply", label="Car jerks or pulls noticeably to left or right")
                ]
            )
        ]
    }
}


class GuidedWizardEngine:
    """Multi-step interactive diagnostic orchestrator."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def get_domain_questions(self, domain: str) -> List[WizardQuestion]:
        config = WIZARD_DOMAINS.get(domain)
        if not config:
            return []
        return config["questions"]

    def evaluate_step(self, request: WizardStepRequest) -> ProblemAnalysisResult:
        domain = request.domain
        answers = request.answers

        config = WIZARD_DOMAINS.get(domain, {
            "title": "Automotive Diagnostic Inspection",
            "subsystem": "General Powertrain"
        })

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        urgency = RiskLevel.MEDIUM
        is_safe = True
        driving_advisory = "Follow step-by-step diagnostic verification before replacing components."
        repair_key = "battery_replacement"

        if domain == "no_start":
            crank = answers.get("crank_behavior", "")
            headlights = answers.get("headlights_test", "")
            fuel = answers.get("fuel_gauge_odor", "")

            if crank in ["rapid_clicking", "slow_crank"] or headlights in ["very_dim", "turn_off_when_cranking"]:
                urgency = RiskLevel.HIGH
                is_safe = False
                driving_advisory = "Vehicle 12V battery is depleted or terminal connections are corroded."
                repair_key = "battery_replacement"
                causes.append(DiagnosticCause(
                    title="Discharged 12V Battery or Corroded Cable Terminals",
                    probability=80,
                    explanation="Insufficient battery cranking amperage causes starter solenoid contacts to rapidly cycle on and off."
                ))
                steps.append(ActionStep(
                    step_number=1,
                    title="Jump-Start Vehicle & Measure Alternator Charging Voltage",
                    description="Connect booster cables to battery posts. Once started, measure battery voltage; must be >13.8V.",
                    tools_needed=["Jumper cables or jump-starter pack", "Multimeter"]
                ))
            elif crank == "single_click_silence":
                urgency = RiskLevel.HIGH
                is_safe = False
                driving_advisory = "Starter motor solenoid contacts burnt or starter motor armature locked."
                repair_key = "starter_motor_replacement"
                causes.append(DiagnosticCause(
                    title="Failed Starter Motor / Burnt Solenoid Contacts",
                    probability=75,
                    explanation="Full battery power reaches starter motor, but internal heavy-amperage copper contacts are burnt."
                ))
            elif crank == "cranks_normal_no_start":
                if fuel == "no_pump_hum":
                    repair_key = "vacuum_leak_repair"
                    causes.append(DiagnosticCause(
                        title="Electric Fuel Pump or Fuel Pump Relay Failure",
                        probability=70,
                        explanation="Engine cranks with good compression and spark, but fuel rail lacks pressurized gasoline.",
                        common_indicators=["No 2-second fuel pump priming buzz when turning ignition to ON"]
                    ))
                else:
                    repair_key = "spark_plugs_ignition_coils"
                    causes.append(DiagnosticCause(
                        title="Loss of Ignition Spark or Crankshaft Position Sensor Signal",
                        probability=65,
                        explanation="Without crankshaft position signal, ECM cannot time spark and injector pulse."
                    ))

        elif domain == "overheating":
            scenario = answers.get("driving_scenario", "")
            heater = answers.get("heater_test", "")
            puddle = answers.get("puddle_or_smoke", "")

            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "Engine overheating detected. Continuing to drive will cause head gasket breach and aluminum head warping."

            if puddle == "white_exhaust_smoke":
                repair_key = "cylinder_head_gasket"
                causes.append(DiagnosticCause(
                    title="Blown Cylinder Head Gasket",
                    probability=90,
                    explanation="Combustion pressure forcing coolant into cylinders, generating sweet white vapor."
                ))
            elif heater == "heater_cold":
                repair_key = "water_pump_replacement"
                causes.append(DiagnosticCause(
                    title="Water Pump Impeller Failure or Trapped Airlock",
                    probability=85,
                    explanation="No coolant reaching cabin heater core proves total loss of cooling system hydraulic circulation."
                ))
            elif scenario == "idle_traffic":
                repair_key = "cooling_fan_motor_relay"
                causes.append(DiagnosticCause(
                    title="Electric Cooling Fan Motor / Relay Failure",
                    probability=80,
                    explanation="Lack of airflow through radiator at low speeds causes rapid temperature spike."
                ))
            else:
                repair_key = "thermostat_replacement"
                causes.append(DiagnosticCause(
                    title="Thermostat Stuck in Closed Position",
                    probability=75,
                    explanation="Thermostat wax element failed, blocking coolant from entering radiator."
                ))

        elif domain == "abnormal_noise":
            ntype = answers.get("noise_type", "")
            ntime = answers.get("noise_timing", "")

            if ntype == "metallic_grinding" and ntime == "only_braking":
                urgency = RiskLevel.HIGH
                is_safe = False
                driving_advisory = "Brake pad backing plate grinding directly against rotor face. Stop driving until repaired."
                repair_key = "brake_pads_rotors_replacement"
                causes.append(DiagnosticCause(
                    title="Exhausted Brake Pad Friction Material (Metal-on-Metal)",
                    probability=95,
                    explanation="Zero friction material remaining. Steel backing plate destroying rotor."
                ))
            elif ntype == "rhythmic_clicking" and ntime == "sharp_turns":
                urgency = RiskLevel.MEDIUM
                repair_key = "cv_axle_replacement"
                causes.append(DiagnosticCause(
                    title="Defective Outer Constant Velocity (CV) Axle Joint",
                    probability=90,
                    explanation="Worn ball raceway inside CV joint clicking under steering articulation angle."
                ))
            elif ntype == "deep_knocking":
                urgency = RiskLevel.CRITICAL
                is_safe = False
                driving_advisory = "Catastrophic engine internal rod bearing failure. Stop engine immediately."
                repair_key = "cylinder_head_gasket"
                causes.append(DiagnosticCause(
                    title="Connecting Rod Bearing Knock / Piston Pin Play",
                    probability=85,
                    explanation="Crankshaft clearance excessive. Immediate risk of throwing rod through engine block."
                ))

        elif domain == "braking_issues":
            pfeel = answers.get("pedal_behavior", "")
            if pfeel == "pedal_sinks":
                urgency = RiskLevel.CRITICAL
                is_safe = False
                driving_advisory = "Brake Master Cylinder is bypassing internally. Complete loss of brakes imminent."
                repair_key = "brake_master_cylinder"
                causes.append(DiagnosticCause(
                    title="Brake Master Cylinder Internal Pressure Leak",
                    probability=85,
                    explanation="Piston seals allowing fluid to bleed backward inside the cylinder."
                ))
            elif pfeel == "pedal_pulsates":
                urgency = RiskLevel.LOW
                repair_key = "brake_pads_rotors_replacement"
                causes.append(DiagnosticCause(
                    title="Warped Brake Rotors / Excessive Lateral Runout",
                    probability=85,
                    explanation="Disc thickness variation kicking hydraulic pulses back into pedal."
                ))

        if not causes:
            causes.append(DiagnosticCause(
                title="Guided Diagnostic Symptom Inconclusive",
                probability=50,
                explanation="Submit additional telemetry or run targeted system analyzers."
            ))

        cost = get_cost_estimate(repair_key, fallback_title=config.get("title", "Automotive Repair"))

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                query_str = f"{domain} {' '.join(answers.values())}"
                rag_resp = retriever.search(query=query_str, top_k=2)
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
            analyzer_id="interactive_guided_wizard",
            analyzer_title=config.get("title", "Interactive Diagnostic Wizard"),
            subsystem=config.get("subsystem", "Vehicle Systems"),
            primary_verdict=f"Wizard Diagnosis: {causes[0].title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary={"domain": domain, "responses": answers},
            rag_reference_chunks=rag_chunks
        )
