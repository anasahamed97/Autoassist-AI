import re
import logging
from typing import List, Dict, Any, Optional

from backend.app.rag.retriever import AutomotiveRetriever
from backend.app.schemas.rag import RAGSearchResultItem
from backend.app.schemas.explanation import SimpleExplanation, DualViewManualResult
from backend.app.services.translation_service import get_translation_service

logger = logging.getLogger(__name__)

_retriever_instance: Optional[AutomotiveRetriever] = None


def _get_shared_retriever() -> AutomotiveRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = AutomotiveRetriever()
    return _retriever_instance


class ExplanationService:
    def __init__(self):
        self.retriever = _get_shared_retriever()

    def explain_query(
        self,
        query: str,
        manufacturer: Optional[str] = None,
        vehicle_model: Optional[str] = None,
        top_k: int = 5,
        language: Optional[str] = "en",
    ) -> DualViewManualResult:
        # Retrieve real technical chunks via existing RAG pipeline
        filters = {}
        if manufacturer and manufacturer != "Generic":
            filters["manufacturer"] = manufacturer
        if vehicle_model and vehicle_model != "Generic" and vehicle_model != "All":
            filters["vehicle_model"] = vehicle_model

        rag_resp = self.retriever.search(
            query=query,
            top_k=top_k,
            similarity_threshold=0.15,
            filters=filters if filters else None,
        )

        passages = rag_resp.results
        simple_explanation = self._synthesize_grounded_explanation(query, passages)

        # Localize explanation if target language is not English
        if language and language != "en":
            simple_explanation = get_translation_service().localize_explanation(
                simple_explanation, query, target_lang=language
            )

        return DualViewManualResult(
            query=query,
            total_matches=len(passages),
            latency_ms=rag_resp.latency_ms,
            technical_passages=passages,
            simple_explanation=simple_explanation,
        )

    def _synthesize_grounded_explanation(
        self, query: str, passages: List[RAGSearchResultItem]
    ) -> SimpleExplanation:
        q_lower = query.lower()

        # Combine text from retrieved chunks for factual grounding
        combined_text = " ".join([p.content for p in passages[:3]]) if passages else ""
        text_lower = combined_text.lower()

        # Domain detection based on query & retrieved manual content
        if any(w in q_lower for w in ["overheat", "temperature", "coolant", "radiator", "thermostat"]) or "coolant" in text_lower:
            return SimpleExplanation(
                what_does_it_mean=(
                    "Your engine is running hotter than its normal operating temperature (typically between 195°F and 220°F / 90°C–105°C). "
                    "The cooling system is unable to transfer combustion heat away from the engine block."
                ),
                why_does_it_happen=(
                    "Possible causes include: low engine coolant level from a leak, a thermostat that is stuck closed, "
                    "an electric radiator fan that isn't turning on, a worn water pump impeller, or an obstructed radiator core."
                ),
                symptoms_you_might_notice=[
                    "Temperature gauge needle climbing into the red danger zone",
                    "Sweet, pungent syrup smell inside or around the engine bay (evaporating coolant)",
                    "Steam or bubbling hissing sounds from the radiator expansion reservoir",
                    "A/C blowing warm air in stop-and-go traffic"
                ],
                what_should_you_do=[
                    "Safely pull off the roadway to a secure location and turn off the engine immediately.",
                    "Turn the cabin heater to maximum heat and blower on high before shutting down if stuck in traffic (this acts as a secondary mini-radiator).",
                    "ALLOW THE ENGINE TO COOL FOR AT LEAST 30–45 MINUTES before touching any cooling components.",
                    "NEVER attempt to unscrew the radiator cap or reservoir cap while the engine is hot—scalding pressurized coolant will spray."
                ],
                when_to_visit_mechanic=(
                    "Visit a workshop immediately if the temperature needle enters the red zone, if you see coolant puddles under the car, "
                    "or if the car overheats repeatedly after cooling down. Driving an overheated engine can warp the cylinder head within minutes."
                ),
                safety_warnings=[
                    "⚠️ Severe scalding hazard: Radiator coolant is under 15+ PSI pressure and exceeds boiling temperature.",
                    "⚠️ Catastrophic engine damage: Severe overheating causes warped cylinder heads and blown head gaskets."
                ],
                suggested_mechanic_questions=[
                    "Did a cooling system pressure test reveal any internal or external coolant leaks?",
                    "Is the thermostat opening fully at its calibrated temperature?",
                    "Did the electric radiator cooling fan motor and relay trigger properly on high speed?",
                    "Is the water pump circulating coolant effectively without bearing play?"
                ]
            )

        elif any(w in q_lower for w in ["battery", "starting", "starter", "alternator", "crank", "voltage"]) or "battery" in text_lower:
            return SimpleExplanation(
                what_does_it_mean=(
                    "Your vehicle's electrical starting and charging system is having difficulty providing the electrical energy needed to start the engine "
                    "or recharge the battery while driving."
                ),
                why_does_it_happen=(
                    "Common causes include: a depleted or aged 12V battery (typically lasting 3–5 years), corroded battery cable terminals, "
                    "a faulty alternator that isn't generating 13.8V–14.6V, a failing starter motor, or a key-off parasitic drain draining the battery overnight."
                ),
                symptoms_you_might_notice=[
                    "Rapid clicking sound when turning the key or pressing Start",
                    "Engine cranks very slowly ('rur-rur-rur') before catching or dying",
                    "Headlights dim when idling and brighten when revving the engine",
                    "Battery or alternator warning light illuminated on the dashboard"
                ],
                what_should_you_do=[
                    "Inspect the battery terminals for white or blue fuzzy corrosion. Clean with a wire brush if safe.",
                    "Check battery resting voltage with a multimeter (12.6V is 100% charged; below 12.0V indicates deep discharge).",
                    "If jump-starting, ensure cables are connected correctly (positive to positive, negative to clean bare chassis ground).",
                    "Avoid running high-draw accessories (seat heaters, high-beam lights) until the charging system is tested."
                ],
                when_to_visit_mechanic=(
                    "Visit an automotive electrician or garage if the battery is over 3 years old, if jump-starting fails, "
                    "or if the battery dies repeatedly overnight (indicating an alternator failure or parasitic draw)."
                ),
                safety_warnings=[
                    "⚠️ Chemical and explosion hazard: Lead-acid batteries contain sulfuric acid and vent flammable hydrogen gas during charging.",
                    "⚠️ Never reverse polarity when jump-starting: this can instantly destroy the vehicle's electronic control modules (ECU)."
                ],
                suggested_mechanic_questions=[
                    "What was the battery's Cold Cranking Amps (CCA) reading compared to its rated capacity?",
                    "Is the alternator delivering between 13.8V and 14.6V under full electrical load?",
                    "Was a key-off parasitic standby drain test performed (should be under 50 mA)?"
                ]
            )

        elif any(w in q_lower for w in ["brake", "pedal", "stopping", "abs", "pad", "rotor"]) or "brake" in text_lower:
            return SimpleExplanation(
                what_does_it_mean=(
                    "Your vehicle's hydraulic braking system is showing symptoms of friction wear, hydraulic pressure loss, "
                    "or disc rotor surface irregularity."
                ),
                why_does_it_happen=(
                    "Common causes include: brake pads worn down near the metal backing plate (<3mm), air bubbles in the hydraulic lines, "
                    "a leaking brake caliper or wheel cylinder, warped rotors causing lateral runout, or low brake fluid in the reservoir."
                ),
                symptoms_you_might_notice=[
                    "High-pitched metallic squealing or scraping noise when applying brakes",
                    "Brake pedal feels spongy, soft, or slowly sinks towards the floorboard",
                    "Steering wheel shakes or pulses when braking from highway speeds",
                    "Vehicle pulls noticeably to the left or right during a stop"
                ],
                what_should_you_do=[
                    "Check the brake fluid reservoir level under the hood (must be between MIN and MAX hashmarks).",
                    "If the pedal sinks to the floor, DO NOT DRIVE. Pumping the pedal repeatedly may build temporary pressure.",
                    "Avoid hard emergency stops and increase following distance significantly.",
                    "Have a technician measure remaining friction thickness in millimeters."
                ],
                when_to_visit_mechanic=(
                    "Visit a workshop immediately if you hear metal-on-metal grinding, if the pedal sinks softly to the floor, "
                    "or if the red Brake warning light or amber ABS light is illuminated."
                ),
                safety_warnings=[
                    "⚠️ Critical safety hazard: Brakes are the most vital active safety system on your vehicle.",
                    "⚠️ Never ignore a spongy or sinking pedal—it indicates hydraulic fluid loss or air contamination."
                ],
                suggested_mechanic_questions=[
                    "What is the exact remaining thickness (in mm) on the inner and outer brake pads?",
                    "Do the brake disc rotors have sufficient thickness above the minimum discard stamp?",
                    "Is the brake fluid moisture content above 2% requiring a hydraulic flush?",
                    "Are the caliper slide pins moving freely without binding?"
                ]
            )

        elif any(w in q_lower for w in ["misfire", "p0300", "p0171", "p0420", "rough", "spark", "idle", "shaking"]) or "misfire" in text_lower:
            return SimpleExplanation(
                what_does_it_mean=(
                    "One or more cylinders in the engine are failing to ignite the air-fuel mixture properly during the power stroke, "
                    "causing unburned fuel to pass into the exhaust and making the engine run roughly."
                ),
                why_does_it_happen=(
                    "Common causes include: worn spark plugs with excessive gap, a cracked or failing direct ignition coil, "
                    "a vacuum leak allowing unmetered air into the intake manifold, or a dirty/clogged fuel injector."
                ),
                symptoms_you_might_notice=[
                    "Engine vibrates, stumbles, or jerks at idle or when accelerating",
                    "Check Engine Light (MIL) is illuminated on the instrument cluster",
                    "Noticeable drop in engine power, throttle response, and fuel economy",
                    "Strong odor of unburned gasoline from the exhaust tailpipe"
                ],
                what_should_you_do=[
                    "Check if the Check Engine Light is STEADY or FLASHING.",
                    "If the light is FLASHING: reduce speed immediately and avoid heavy acceleration—a flashing light means raw fuel is entering and overheating the catalytic converter.",
                    "Have an OBD-II scanner read the stored fault codes (e.g. P0300 for random misfire, P0301 for cylinder 1).",
                    "Do not drive on long road trips until the misfire source is resolved."
                ],
                when_to_visit_mechanic=(
                    "Visit a mechanic promptly. Driving with a continuous misfire will quickly overheat and destroy the expensive catalytic converter (₹25,000–₹60,000 replacement)."
                ),
                safety_warnings=[
                    "⚠️ Flashing Check Engine Light warning: Raw unburned fuel can ignite inside the catalytic converter, creating fire hazard and melt damage."
                ],
                suggested_mechanic_questions=[
                    "Which specific cylinder is registering the misfire count on live data?",
                    "Did a resistance and primary/secondary spark test verify the ignition coil?",
                    "Are Long Term Fuel Trims (LTFT) showing a vacuum leak (positive trim at idle)?",
                    "What is the physical condition and color of the spark plug electrodes?"
                ]
            )

        else:
            # Generic Grounded Manual Synthesis
            first_passage = passages[0].content if passages else "Refer to vehicle manufacturer service guide."
            clean_excerpt = re.sub(r"\s+", " ", first_passage[:280]).strip()

            return SimpleExplanation(
                what_does_it_mean=(
                    f"This technical issue relates to: '{query}'. In simple terms, your vehicle is experiencing an operating condition "
                    f"described in manufacturer technical documentation: \"{clean_excerpt}...\""
                ),
                why_does_it_happen=(
                    "Automotive systems operate under tight physical tolerances. Symptoms typically occur when mechanical components "
                    "experience wear, electrical sensors read out-of-range voltages, or fluids degrade past their service life."
                ),
                symptoms_you_might_notice=[
                    "Abnormal sound, vibration, or dashboard warning indicator",
                    "Change in pedal feel, engine response, or vehicle handling",
                    "Subtle changes in fuel consumption or operating temperature"
                ],
                what_should_you_do=[
                    "Document the exact driving conditions when the symptom occurs (speed, gear, cold vs warm engine).",
                    "Inspect visible fluid levels (engine oil, coolant, brake fluid) on level ground.",
                    "Avoid aggressive acceleration or high-speed driving until diagnosed.",
                    "Review the technical manual excerpts below to understand the factory-specified procedure."
                ],
                when_to_visit_mechanic=(
                    "Schedule an inspection if warning lights remain on, if fluid levels drop without explanation, "
                    "or if you notice metallic noises or loss of braking/steering response."
                ),
                safety_warnings=[
                    "⚠️ General safety note: Never work on an engine with running belts or a hot pressurized cooling system."
                ],
                suggested_mechanic_questions=[
                    f"What did the physical inspection reveal regarding '{query}'?",
                    "Can you show me the worn component and explain why replacement is necessary?",
                    "Are there OEM or verified aftermarket replacement options available?"
                ]
            )


_explanation_service_instance = None


def get_explanation_service() -> ExplanationService:
    global _explanation_service_instance
    if _explanation_service_instance is None:
        _explanation_service_instance = ExplanationService()
    return _explanation_service_instance
