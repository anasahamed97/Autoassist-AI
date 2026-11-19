"""
AutoAssist AI - NVH Sound & Vibration Acoustic Problem Analyzer
Classifies automotive acoustic anomalies, vibrations, and isolates failing mechanical components.
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


class AcousticAnalysisRequest(BaseModel):
    sound_type: str = Field(
        ...,
        description="'squeal_chirp', 'grind_metal', 'click_tick', 'knock_thump', 'whine_hum', 'hiss_air', 'clunk_pop'"
    )
    location: str = Field(
        ...,
        description="'front_wheel_brakes', 'engine_front_belt', 'engine_internal_block', 'transmission_tunnel', 'under_car_exhaust', 'steering_suspension', 'inside_dash'"
    )
    condition: str = Field(
        ...,
        description="'when_braking', 'when_turning', 'accelerating', 'cold_start', 'over_bumps', 'idle_park', 'highway_cruising'"
    )
    speed_dependent: bool = Field(default=False, description="Does pitch or frequency increase with vehicle speed?")
    rpm_dependent: bool = Field(default=False, description="Does pitch or frequency increase with engine RPM?")
    include_rag_chunks: bool = True


class AcousticProblemAnalyzer:
    """Isolates automotive mechanical defects via sound frequency and operational patterns."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def analyze(self, request: AcousticAnalysisRequest) -> ProblemAnalysisResult:
        urgency = RiskLevel.MEDIUM
        is_safe = True
        driving_advisory = "Drive moderately; have component inspected before mechanical seizure occurs."
        repair_key = "brake_pads_rotors_replacement"

        causes: List[DiagnosticCause] = []
        steps: List[ActionStep] = []
        telemetry: Dict[str, Any] = {
            "sound": request.sound_type,
            "location": request.location,
            "condition": request.condition,
            "speed_dependent": request.speed_dependent,
            "rpm_dependent": request.rpm_dependent,
        }

        # Case 1: Deep knock in engine block (Rod Bearing Knock - CRITICAL)
        if request.sound_type == "knock_thump" and request.location == "engine_internal_block":
            urgency = RiskLevel.CRITICAL
            is_safe = False
            driving_advisory = "EMERGENCY: Suspected engine connecting rod bearing failure! Stop driving immediately. Continuing to run engine will throw a rod through the engine block, completely destroying the engine."
            repair_key = "cylinder_head_gasket"
            causes.append(DiagnosticCause(
                title="Connecting Rod Bearing Failure / Spun Bearing",
                probability=75,
                explanation="Excessive clearance between crankshaft journal and connecting rod bearing cap causes metal-on-metal impact at double engine RPM.",
                common_indicators=["Deep rhythmic thud that gets louder under acceleration load", "Low oil pressure warning lamp illuminated"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Perform Cylinder Power Balance Kill Test",
                description="Use scan tool or disconnect coil connectors one by one. If knocking sound drops significantly when a specific cylinder is cut, that cylinder's rod bearing is spun.",
                tools_needed=["Bi-directional scan tool or insulated spark plug pliers"]
            ))

        # Case 2: Metal Grinding when braking (Worn out Brake Pads)
        elif request.sound_type == "grind_metal" and (request.location == "front_wheel_brakes" or request.condition == "when_braking"):
            urgency = RiskLevel.HIGH
            is_safe = False
            driving_advisory = "CRITICAL: Brake friction material is completely worn to bare steel backing plate. Severe gouging of rotors and increased stopping distance. Replace immediately."
            repair_key = "brake_pads_rotors_replacement"
            causes.append(DiagnosticCause(
                title="Brake Pad Friction Material Worn to Metal Backing Plate",
                probability=85,
                explanation="Friction lining has completely degraded. Steel brake pad backing plate is pressing directly against cast iron brake rotor face.",
                common_indicators=["Deep metallic grinding rasp when pressing pedal", "Visible grooving on rotor surface"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Visual Pad and Rotor Thickness Inspection",
                description="Remove wheel and inspect inner and outer brake pads. Pad thickness <2mm requires immediate replacement of pads and rotors.",
                tools_needed=["Tire iron / lug wrench", "Jack stands", "Brake pad thickness gauge"]
            ))

        # Case 3: High-pitched squeal when braking (Wear Indicator)
        elif request.sound_type == "squeal_chirp" and request.condition == "when_braking":
            urgency = RiskLevel.MEDIUM
            is_safe = True
            driving_advisory = "Safe to drive for up to 500 miles. Brake pads have reached wear indicator limit (approx 2-3mm remaining)."
            repair_key = "brake_pads_rotors_replacement"
            causes.append(DiagnosticCause(
                title="Acoustic Brake Pad Wear Sensor Indicator Contacting Rotor",
                probability=80,
                explanation="Built-in spring steel acoustic tab is intentionally designed to emit a high-pitched squeal when pad thickness reaches 2.5mm.",
                common_indicators=["Continuous screeching sound while applying brakes, quiets when letting off"]
            ))

        # Case 4: High-pitched squeal from front of engine (Serpentine Belt / Tensioner)
        elif request.sound_type == "squeal_chirp" and request.location == "engine_front_belt":
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Drive with caution. If belt snaps, power steering, water pump, and alternator charging will be instantly lost."
            repair_key = "alternator_replacement"
            causes.append(DiagnosticCause(
                title="Worn or Slipping Serpentine Accessory Drive Belt",
                probability=70,
                explanation="Hardened, glazed, or oil-soaked EPDM rubber belt slips across alternator or A/C compressor pulleys, especially on cold starts.",
                common_indicators=["Loud screech at cold morning startup or when turning steering wheel to full lock"]
            ))
            causes.append(DiagnosticCause(
                title="Seized or Weak Automatic Belt Tensioner Pulley",
                probability=30,
                explanation="Tensioner spring has weakened, failing to maintain specified 80–120 lbs of belt tension."
            ))

        # Case 5: Clicking / snapping on sharp turns (Outer CV Axle)
        elif request.sound_type == "click_tick" and (request.condition == "when_turning" or request.location == "front_wheel_brakes"):
            urgency = RiskLevel.HIGH
            driving_advisory = "Avoid sharp high-torque turns. Outer CV joint may bind or separate, stranding vehicle without drive wheel torque."
            repair_key = "cv_axle_replacement"
            causes.append(DiagnosticCause(
                title="Defective Constant Velocity (CV) Axle Joint",
                probability=85,
                explanation="Torn rubber boot allowed moly grease to sling out and road sand to enter, causing severe galling in the steel ball raceway.",
                common_indicators=["Rhythmic click-click-click noise that speeds up when accelerating through a tight turn into a driveway or parking space"]
            ))
            steps.append(ActionStep(
                step_number=1,
                title="Inspect CV Axle Accordion Boot for Tears",
                description="Turn front wheel to full lock. Look behind the wheel knuckle for dark grease splattered inside the wheel well.",
                tools_needed=["Flashlight", "Inspection mirror"]
            ))

        # Case 6: Whining / roaring that changes with vehicle speed (Wheel Bearing)
        elif (request.sound_type == "whine_hum" or request.sound_type == "grind_metal") and request.speed_dependent:
            urgency = RiskLevel.MEDIUM
            driving_advisory = "Have wheel bearing replaced within 250 miles. Severely degraded bearings can overheat and seize."
            repair_key = "wheel_bearing_hub_assembly"
            causes.append(DiagnosticCause(
                title="Damaged Wheel Hub Bearing Assembly",
                probability=75,
                explanation="Spalling and micro-pitting on inner and outer bearing races produce a deep roaring or humming that mimics an airplane propeller.",
                common_indicators=["Sound changes pitch when gently swaying steering left and right at 45 MPH"]
            ))

        # Case 7: Clunking / rattling over bumps (Sway Bar Links or Struts)
        elif request.sound_type == "clunk_pop" and request.condition == "over_bumps":
            urgency = RiskLevel.LOW
            driving_advisory = "Drivable. Causes annoying rattling on uneven roads, but unlikely to cause immediate breakdown."
            repair_key = "sway_bar_links_bushing"
            causes.append(DiagnosticCause(
                title="Worn Sway Bar (Stabilizer) End Links or Bushings",
                probability=65,
                explanation="Miniature ball-and-socket joints in end links have lost internal nylon seating, clattering whenever one wheel hits a bump.",
                common_indicators=["Loose hollow thud over potholes and driveway curbs"]
            ))
            causes.append(DiagnosticCause(
                title="Worn Lower Ball Joint or Strut Mount Bearing",
                probability=35,
                explanation="Rubber mount collapsed or ball joint radial play."
            ))

        # Case 8: Rapid clicking behind dashboard (Blend Door Actuator)
        elif request.sound_type == "click_tick" and request.location == "inside_dash":
            urgency = RiskLevel.LOW
            driving_advisory = "Cosmetic / comfort issue. Fully safe to drive."
            repair_key = "blend_door_actuator"
            causes.append(DiagnosticCause(
                title="Stripped HVAC Temperature / Blend Door Actuator Gear",
                probability=90,
                explanation="Plastic gears inside electric stepper motor stripped, jumping teeth upon key-on climate sweep.",
                common_indicators=["Rapid rhythmic clicking for 15-30 seconds after turning ignition on"]
            ))

        # Default fallback
        if not causes:
            causes.append(DiagnosticCause(
                title="Mechanical Vibration or Acoustic Resonance",
                probability=50,
                explanation=f"Acoustic signature ({request.sound_type}) at {request.location} suggests localized mechanical wear."
            ))

        total_p = sum(c.probability for c in causes)
        if total_p > 0:
            for c in causes:
                c.probability = int(round((c.probability / total_p) * 100))

        cost = get_cost_estimate(repair_key, fallback_title="Acoustic Repair")

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                rag_resp = retriever.search(query=f"noise symptom {request.sound_type} {request.location} {request.condition}", top_k=2)
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
            analyzer_id="acoustic_nvh_analyzer",
            analyzer_title="NVH Sound & Vibration Acoustic Problem Analyzer",
            subsystem="Acoustics & Mechanical Powertrain / Chassis",
            primary_verdict=f"Acoustic Isolation: {causes[0].title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
