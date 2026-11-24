import re
import logging
from typing import Dict, Any, List
from backend.app.schemas.severity import SeverityRequest, SeverityResponse

logger = logging.getLogger(__name__)

# Keywords triggering critical safety warnings
CRITICAL_TRIGGERS = [
    "brake failure", "pedal sinks", "pedal sinking", "sinking to floor", "sinks to floor",
    "no brakes", "brake sinking", "fluid leak", "fuel leak", "brake fluid",
    "gasoline smell", "raw fuel", "smoke", "fire", "burning", "boiling", "overheating red",
    "steering lock", "loss of control", "rod knock", "low oil pressure", "engine seized",
    "brakes failed", "pedal to floor", "spongy sinking"
]

MODERATE_TRIGGERS = [
    "check engine", "misfire", "p0300", "p0171", "p0420", "shudder", "slipping",
    "squeal", "grinding", "whine", "vibration", "spongy brake", "coolant low",
    "dead battery", "alternator", "stuck thermostat", "rough idle", "exhaust smoke"
]


class SeverityService:
    def assess_severity(self, req: SeverityRequest) -> SeverityResponse:
        text = req.symptom_or_code.lower().strip()

        # Check explicit overrides first
        is_critical = False
        reasons: List[str] = []
        warning_signs: List[str] = []

        if not req.can_vehicle_steer_and_stop:
            is_critical = True
            reasons.append("Reported impairment of braking or steering control represents an immediate physical road hazard.")
            warning_signs.append("Inability to bring vehicle to a controlled stop or maintain lane position.")

        if req.smoke_or_fire_detected:
            is_critical = True
            reasons.append("Active smoke, fire risk, or fuel odor indicates imminent combustion or electrical short hazard.")
            warning_signs.append("Smoke from engine bay, burning acrid odor, or gasoline fumes.")

        if req.temperature_in_red:
            is_critical = True
            reasons.append("Engine temperature operating in the red danger zone risks cylinder head warpage and catastrophic engine seizure.")
            warning_signs.append("Coolant temperature needle at maximum, boiling reservoir, or steam escaping.")

        # Keyword inspection with word boundaries (avoids 'fire' matching 'misfire')
        for crit in CRITICAL_TRIGGERS:
            if re.search(r'\b' + re.escape(crit) + r'\b', text):
                is_critical = True
                reasons.append(f"Reported symptom pattern matches critical threshold: '{crit}'.")
                break

        if is_critical:
            return SeverityResponse(
                category="CRITICAL",
                badge_title="CRITICAL – Immediate Safety Attention",
                is_safe_to_drive=False,
                urgency_level="Immediate / Do Not Drive",
                rationale=" ".join(reasons) or "Automotive subsystem exhibits failure mode that compromises basic vehicle safety.",
                warning_signs=warning_signs or [
                    "Loss of hydraulic braking firmness",
                    "Rapid engine overheating or steam discharge",
                    "Fuel leaks or raw gasoline fumes in engine bay",
                    "Severe metallic engine knocking or oil pressure light"
                ],
                immediate_action="Safely pull off the roadway, switch off ignition immediately, and do not attempt to continue driving. Arrange roadside assistance or flatbed towing.",
                mechanic_visit_advice="Immediate professional workshop inspection is mandatory before the vehicle can be safely operated.",
                stop_driving_notice="⚠️ DO NOT DRIVE HAZARD: Continued operation carries severe risk of accidents, engine destruction, or vehicle fire."
            )

        # Check Moderate
        is_moderate = False
        for mod in MODERATE_TRIGGERS:
            if mod in text:
                is_moderate = True
                reasons.append(f"Symptom correlates with active mechanical fault: '{mod}'.")

        if is_moderate or req.subsystem.lower() in ["brakes", "transmission", "cooling", "electrical"]:
            return SeverityResponse(
                category="MODERATE",
                badge_title="MODERATE – Inspection Recommended",
                is_safe_to_drive=True,
                urgency_level="Within 7 - 14 Days",
                rationale=" ".join(reasons) or "Vehicle exhibits abnormal performance symptoms that may accelerate component wear or degrade fuel economy if left unaddressed.",
                warning_signs=[
                    "Illuminated Check Engine Light (steady, non-flashing)",
                    "Subsystem performance degradation or unusual operating noises",
                    "Minor coolant or oil seepage without sudden fluid loss",
                    "Intermittent starting hesitation or battery age fatigue"
                ],
                immediate_action="Drive with extra caution. Avoid high-speed highway driving or heavy towing until checked. Schedule an appointment with a qualified mechanic.",
                mechanic_visit_advice="Schedule inspection within 7 to 14 days to prevent minor wear from becoming an expensive secondary failure.",
                stop_driving_notice=None
            )

        # Default Low
        return SeverityResponse(
            category="LOW",
            badge_title="LOW – General Attention",
            is_safe_to_drive=True,
            urgency_level="Next Scheduled Service",
            rationale="Reported symptom represents routine maintenance, minor cosmetic wear, or non-urgent operational observation.",
            warning_signs=[
                "Scheduled service interval approaching",
                "Minor cabin filter or wiper blade wear",
                "Non-critical cosmetic or minor operational query"
            ],
            immediate_action="Vehicle is safe to drive under normal conditions. Monitor fluid levels and address at your next routine service interval.",
            mechanic_visit_advice="Discuss at your next routine oil change or scheduled maintenance visit.",
            stop_driving_notice=None
        )


_severity_service_instance = None


def get_severity_service() -> SeverityService:
    global _severity_service_instance
    if _severity_service_instance is None:
        _severity_service_instance = SeverityService()
    return _severity_service_instance
