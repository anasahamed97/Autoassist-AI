"""
AutoAssist AI - OBD-II Diagnostic Trouble Code (DTC) Analyzer
Analyzes generic and manufacturer OBD-II codes with freeze-frame sensor interpretation.
"""
import re
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


class FreezeFrameInput(BaseModel):
    engine_rpm: Optional[int] = Field(None, description="Engine RPM at fault trigger (e.g. 750 or 2500)")
    vehicle_speed_mph: Optional[int] = Field(None, description="Speed in MPH")
    short_term_fuel_trim_pct: Optional[float] = Field(None, description="STFT in % (-25.0 to +25.0)")
    long_term_fuel_trim_pct: Optional[float] = Field(None, description="LTFT in % (-25.0 to +25.0)")
    engine_coolant_temp_f: Optional[float] = Field(None, description="ECT in Fahrenheit")
    calculated_load_pct: Optional[float] = Field(None, description="Calculated engine load %")
    maf_flow_rate_gps: Optional[float] = Field(None, description="Grams per second (e.g. 2.5 to 150.0)")
    battery_voltage: Optional[float] = Field(None, description="System voltage during trigger")


class DTCAnalysisRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=10, description="DTC code, e.g., P0300, P0171, C0035, U0100")
    symptoms: Optional[str] = Field(None, description="Customer-reported symptoms, e.g. rough idle, shaking")
    freeze_frame: Optional[FreezeFrameInput] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    include_rag_chunks: bool = True


# Detailed Knowledge Base of Top Automotive DTC Codes
KNOWN_DTC_DATABASE: Dict[str, Dict[str, Any]] = {
    "P0300": {
        "title": "Random / Multiple Cylinder Misfire Detected",
        "subsystem": "Ignition & Combustion System",
        "urgency": RiskLevel.HIGH,
        "is_safe": False,
        "driving_advisory": "Flashing check engine light indicates raw unburned fuel is entering and destroying the catalytic converter. Stop driving immediately.",
        "repair_key": "spark_plugs_ignition_coils",
        "causes": [
            ("Worn or fouled spark plugs / Incorrect spark plug gap", 35, "Spark plugs lose electrode material over 60,000-100,000 miles, requiring higher secondary coil voltage to jump gap."),
            ("Failing ignition coil packs or boots", 25, "Coil insulation breaks down under thermal load causing intermittent spark misfire."),
            ("Intake manifold or vacuum leak (unmetered air)", 20, "Lean air-fuel mixture fails to ignite cleanly at idle."),
            ("Low fuel pressure or clogged fuel filter/injectors", 12, "Insufficient fuel atomization under engine load."),
            ("Low cylinder compression (valves or piston rings)", 8, "Mechanical loss of compression prevents thermal combustion threshold.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Inspect Spark Plugs and Ignition Coils",
                description="Remove spark plugs and check for carbon fouling, oil wetting, or excessive electrode gap (>0.044 inch). Check rubber coil boots for spark arcing tracks.",
                tools_needed=["5/8 spark plug socket", "Feeler gauge", "Ratchet extension"]
            ),
            ActionStep(
                step_number=2,
                title="Evaluate Long Term Fuel Trims (LTFT)",
                description="If LTFT exceeds +15% at idle, perform an intake smoke test to detect unmetered air vacuum leaks.",
                tools_needed=["OBD-II live data scanner", "Automotive smoke machine"]
            ),
            ActionStep(
                step_number=3,
                title="Perform Relative Compression Test",
                description="Disable fuel pump fuse and crank engine while listening for even cadence, or connect compression gauge to verify all cylinders are within 10% of each other.",
                tools_needed=["Cylinder compression test gauge", "Fuel pump fuse puller"]
            )
        ]
    },
    "P0301": {
        "title": "Cylinder 1 Misfire Detected",
        "subsystem": "Ignition & Combustion System",
        "urgency": RiskLevel.HIGH,
        "is_safe": False,
        "driving_advisory": "Severe misfire on Cylinder 1. Avoid heavy acceleration to prevent catalytic converter damage.",
        "repair_key": "spark_plugs_ignition_coils",
        "causes": [
            ("Defective Cylinder 1 Ignition Coil Pack", 45, "Ignition coil internal winding breakdown or arcing boot."),
            ("Fouled or Damaged Spark Plug in Cylinder 1", 30, "Carbon, oil or fuel deposits preventing spark."),
            ("Cylinder 1 Fuel Injector Clogged or Stuck Closed", 15, "Lack of fuel delivery to cylinder 1."),
            ("Cylinder 1 Valve or Compression Issue", 10, "Intake/exhaust valve carbon deposit or leaking head gasket.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Coil Swap Diagnostic Test",
                description="Swap ignition coil #1 with ignition coil #2. Clear DTC codes and run engine. If code switches to P0302, coil #1 is definitely bad and must be replaced.",
                tools_needed=["10mm socket", "OBD-II scanner"]
            ),
            ActionStep(
                step_number=2,
                title="Inspect Cylinder 1 Spark Plug",
                description="Remove plug #1. Compare with other cylinders. Look for wet gas, oil or black carbon.",
                tools_needed=["Spark plug socket", "Ratchet"]
            )
        ]
    },
    "P0171": {
        "title": "System Too Lean (Bank 1)",
        "subsystem": "Fuel & Air Metering System",
        "urgency": RiskLevel.MEDIUM,
        "is_safe": True,
        "driving_advisory": "Safe for short trips to service facility; avoid towing or wide-open throttle acceleration.",
        "repair_key": "vacuum_leak_repair",
        "causes": [
            ("Unmetered Vacuum Leak (Intake Gasket, PCV Hose, Brake Booster)", 40, "Air enters intake manifold downstream of the Mass Airflow Sensor, diluting air/fuel ratio."),
            ("Dirty or Contaminated Mass Airflow (MAF) Sensor", 30, "Dust or oil coat the heated wire, causing it to under-report incoming air volume to ECM."),
            ("Weak Fuel Pump or Clogged Fuel Filter", 15, "Insufficient fuel rail pressure cannot deliver commanded fuel volume."),
            ("Faulty Upstream Oxygen / Air-Fuel Ratio Sensor", 10, "Sensor degraded and falsely reporting excessive oxygen in exhaust."),
            ("Exhaust Leak Before Upstream O2 Sensor", 5, "Atmospheric oxygen drawn into exhaust manifold pulse.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Compare Fuel Trim at Idle vs 2500 RPM",
                description="Read LTFT in live data. If LTFT is +20% at idle and drops to +4% at 2500 RPM, you have a VACUUM LEAK. If LTFT remains +20% at 2500 RPM, you have a FUEL DELIVERY / MAF issue.",
                tools_needed=["OBD-II scanner with Live PID display"]
            ),
            ActionStep(
                step_number=2,
                title="Clean MAF Sensor Wire",
                description="Spray Mass Airflow Sensor wire with dedicated CRC MAF cleaner aerosol. Never touch the wire with cotton swabs or fingers.",
                tools_needed=["MAF sensor cleaner spray", "Torx security bit"]
            ),
            ActionStep(
                step_number=3,
                title="Smoke Test Intake Tract",
                description="Inject smoke into brake booster vacuum hose. Watch for smoke escaping from PCV valve, oil dipstick tube, or intake manifold runners.",
                tools_needed=["Smoke generator machine"]
            )
        ]
    },
    "P0420": {
        "title": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "subsystem": "Exhaust & Emissions Control",
        "urgency": RiskLevel.MEDIUM,
        "is_safe": True,
        "driving_advisory": "Vehicle is drivable but will not pass state emissions inspection. Engine emissions are elevated.",
        "repair_key": "catalytic_converter",
        "causes": [
            ("Depleted Catalytic Converter Cerium / Platinum Substrate", 65, "The washcoat has lost oxygen storage capacity, causing downstream O2 sensor to mimic upstream O2 sensor."),
            ("Exhaust Leak Directly Near Catalytic Converter", 15, "Cracked exhaust flange or flex pipe drawing ambient air into exhaust stream."),
            ("Faulty Downstream Oxygen Sensor (O2 Sensor)", 10, "Sensor lazy or drifted in calibration (verify with scan tool graph before replacing!)."),
            ("Previous Engine Misfire or Oil Burning", 10, "Unburned fuel or phosphorus from motor oil poisoned catalytic honeycomb.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Graph Upstream vs Downstream O2 Sensors",
                description="Warm engine fully. Upstream O2 sensor should switch rapidly between 0.1V and 0.9V. Downstream sensor should maintain a steady line around 0.6V to 0.7V. If downstream sensor switches rapidly like upstream, catalytic efficiency is degraded.",
                tools_needed=["OBD-II Graphing Scanner or Scope"]
            ),
            ActionStep(
                step_number=2,
                title="Inspect Exhaust Flanges for Leaks",
                description="Look for black carbon soot around catalytic converter flanges and flex pipe.",
                tools_needed=["Inspection light", "Spray bottle of soapy water"]
            )
        ]
    },
    "P0128": {
        "title": "Coolant Thermostat (Coolant Temp Below Regulating Temperature)",
        "subsystem": "Engine Cooling System",
        "urgency": RiskLevel.LOW,
        "is_safe": True,
        "driving_advisory": "Drivable. Engine runs slightly cooler than optimal, causing 5-10% reduced fuel economy and weak cabin heater output.",
        "repair_key": "thermostat_replacement",
        "causes": [
            ("Thermostat Stuck in Partially Open Position", 75, "Spring fatigue or broken rubber seal allows continuous coolant flow through radiator before engine reaches operating temp."),
            ("Defective Engine Coolant Temperature (ECT) Sensor", 15, "Sensor thermistor has drifted out of calibration."),
            ("Low Coolant Level / Trapped Air Bubble", 10, "Air pocket around ECT sensor prevents accurate liquid temperature measurement.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Monitor Warm-Up with Infrared Thermometer",
                description="Measure upper radiator hose temperature during cold start. The hose should remain cool until engine hits 185°F (85°C), then surge hot. If it warms up gradually from start, thermostat is stuck open.",
                tools_needed=["Infrared non-contact pyrometer"]
            ),
            ActionStep(
                step_number=2,
                title="Replace Thermostat and Gasket",
                description="Install OEM thermostat with jiggle pin positioned at the 12 o'clock position to allow trapped air to bleed through.",
                tools_needed=["10mm socket", "Coolant drain pan", "Fresh 50/50 coolant"]
            )
        ]
    },
    "P0455": {
        "title": "Evaporative Emission System (EVAP) - Gross Leak Detected",
        "subsystem": "Fuel Vapor & Emissions",
        "urgency": RiskLevel.LOW,
        "is_safe": True,
        "driving_advisory": "Fully safe to drive. Harmless to powertrain, but will fail emissions testing.",
        "repair_key": "vacuum_leak_repair",
        "causes": [
            ("Loose, Missing, or Degraded Fuel Tank Filler Cap", 60, "Rubber O-ring on gas cap dried out, cracked, or cap not clicked tight."),
            ("EVAP Vent Solenoid Valve Stuck Open", 20, "Road dirt or rust jamming vent valve plunger underneath vehicle near charcoal canister."),
            ("EVAP Purge Solenoid Stuck Open under Hood", 12, "Purge valve leaks vacuum from intake manifold into fuel tank continuously."),
            ("Cracked or Disconnected EVAP Vapor Hose", 8, "Vapor recovery hose damaged or detached.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Inspect and Retighten Fuel Filler Cap",
                description="Check rubber seal for cracks. Clean filler neck rim. Tighten until at least 3 distinct clicks are heard. Clear code and drive for 2 drive cycles.",
                tools_needed=["Lint-free rag"]
            ),
            ActionStep(
                step_number=2,
                title="Test Purge Solenoid for Vacuum Hold",
                description="Remove EVAP purge valve from engine bay. Apply hand vacuum pump to inlet port: it should hold vacuum with no electrical power applied. If vacuum drops, valve is leaking.",
                tools_needed=["Hand vacuum pump (Mityvac)"]
            )
        ]
    },
    "P0562": {
        "title": "System Voltage Low",
        "subsystem": "Starting & Charging System",
        "urgency": RiskLevel.HIGH,
        "is_safe": False,
        "driving_advisory": "Vehicle running entirely on declining battery reserve. Engine may stall abruptly when battery depletes.",
        "repair_key": "alternator_replacement",
        "causes": [
            ("Failing Alternator (Worn Brushes / Blown Diodes)", 55, "Alternator cannot maintain system voltage above 13.5V while engine runs."),
            ("Corroded or Loose Battery Terminals / Ground Straps", 25, "High electrical resistance drops voltage between alternator and PCM."),
            ("Slipping or Broken Serpentine Drive Belt", 15, "Belt loose or automatic tensioner spring seized."),
            ("Sulfated or Shorted Battery Cell", 5, "Internal plate short drags system voltage down.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Check Charging Voltage at Battery",
                description="Measure DC voltage across battery terminals while engine is idling with headlights and A/C on. Voltage must be between 13.8V and 14.6V. If under 13.0V, alternator charging system is defective.",
                tools_needed=["Digital multimeter"]
            )
        ]
    },
    "C0035": {
        "title": "Left Front Wheel Speed Sensor Circuit Fault",
        "subsystem": "Braking & ABS Traction Control",
        "urgency": RiskLevel.MEDIUM,
        "is_safe": True,
        "driving_advisory": "Standard hydraulic braking remains functional, but ABS anti-skid and Traction Control are disabled. Drive with increased stopping distance.",
        "repair_key": "wheel_bearing_hub_assembly",
        "causes": [
            ("Wheel Speed Sensor Wiring Harness Damaged or Corroded", 40, "Wheel articulation stretches or breaks copper wiring inside harness."),
            ("Debris / Metal Shavings on Magnetic Tone Ring", 30, "Brake dust or rust flakes interfering with magnetic reluctance signal."),
            ("Failed Wheel Speed Sensor Hall-Effect Element", 20, "Internal sensor electronics failed due to moisture intrusion."),
            ("Worn Wheel Bearing Allowing Excessive Air Gap", 10, "Bearing play tilts tone ring away from sensor tip.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="Inspect Sensor Wiring and Connector",
                description="Examine wiring harness routed along strut tower for pinch points, chafing against tire rim, or green corrosion in plug.",
                tools_needed=["Inspection light", "Contact cleaner"]
            )
        ]
    },
    "U0100": {
        "title": "Lost Communication with ECM / PCM",
        "subsystem": "CAN Bus & Network Communication",
        "urgency": RiskLevel.HIGH,
        "is_safe": False,
        "driving_advisory": "CAN communication breakdown. Gauges, transmission shifting, and throttle response may become erratic.",
        "repair_key": "parasitic_draw_repair",
        "causes": [
            ("Blown ECM/PCM Power Relay or Main Fuse", 40, "No electrical power feeding main engine control module."),
            ("Damaged CAN-High or CAN-Low Twisted Pair Wiring", 30, "Short to ground, short to 12V, or open circuit along CAN backbone."),
            ("Corroded Main Ground Terminal at Engine Block or Chasis", 20, "ECM ground reference floating, creating signal corruption."),
            ("Internal ECM Hardware Failure", 10, "Component failure inside powertrain control module.")
        ],
        "steps": [
            ActionStep(
                step_number=1,
                title="CAN Bus Termination Resistance Test",
                description="Disconnect vehicle 12V battery. Measure resistance between OBD-II Pin 6 (CAN-H) and Pin 14 (CAN-L). A healthy CAN bus measures exactly 60 Ohms (two 120-Ohm terminating resistors in parallel).",
                tools_needed=["Digital multimeter", "OBD-II breakout box or fine test probes"]
            )
        ]
    }
}


class DTCProblemAnalyzer:
    """Intelligent OBD-II trouble code analyzer with freeze-frame calculation and RAG integration."""

    def __init__(self):
        self.retriever = None

    def _get_retriever(self) -> AutomotiveRetriever:
        if self.retriever is None:
            self.retriever = AutomotiveRetriever()
        return self.retriever

    def analyze(self, request: DTCAnalysisRequest) -> ProblemAnalysisResult:
        clean_code = request.code.strip().upper()
        # Normalize code format, e.g. "p0300" -> "P0300"
        m = re.search(r"([PBCU]\d{4}[A-Z]?)", clean_code)
        if m:
            clean_code = m.group(1)

        known = KNOWN_DTC_DATABASE.get(clean_code)

        # Fallback for generic or unknown code
        if not known:
            domain_char = clean_code[0] if clean_code else "P"
            domain_map = {
                "P": "Powertrain (Engine/Transmission/Emissions)",
                "C": "Chassis (ABS/Brakes/Steering/Suspension)",
                "B": "Body (Airbags/Climate/Lighting)",
                "U": "Network Communication (CAN Bus/Modules)"
            }
            subsystem = domain_map.get(domain_char, "Automotive Powertrain")
            
            title = f"Diagnostic Trouble Code {clean_code}"
            urgency = RiskLevel.MEDIUM
            is_safe = True
            driving_advisory = "Drive cautiously to an inspection facility for complete live-data scan."
            repair_key = "spark_plugs_ignition_coils"

            causes = [
                DiagnosticCause(
                    title=f"Subsystem Sensor or Circuit Malfunction ({clean_code})",
                    probability=60,
                    explanation=f"The Powertrain Control Module flagged an out-of-range signal for code {clean_code}."
                ),
                DiagnosticCause(
                    title="Wiring Harness Chafing or Poor Connector Pin Fitment",
                    probability=25,
                    explanation="Intermittent open circuit or ground resistance triggering fault code."
                ),
                DiagnosticCause(
                    title="Auxiliary Component Degradation",
                    probability=15,
                    explanation="Mechanical or thermal fatigue in associated system."
                )
            ]
            steps = [
                ActionStep(
                    step_number=1,
                    title=f"Retrieve Live Sensor Telemetry for {clean_code}",
                    description=f"Connect a bidirectional scan tool to inspect freeze-frame conditions when {clean_code} set.",
                    tools_needed=["OBD-II Diagnostic Scanner"]
                ),
                ActionStep(
                    step_number=2,
                    title="Inspect Wiring Harness & Ground Terminals",
                    description="Inspect harness routing near hot exhaust and vibrating brackets for rub-through damage.",
                    tools_needed=["Inspection light", "Digital multimeter"]
                )
            ]
        else:
            title = known["title"]
            subsystem = known["subsystem"]
            urgency = known["urgency"]
            is_safe = known["is_safe"]
            driving_advisory = known["driving_advisory"]
            repair_key = known["repair_key"]

            causes = [
                DiagnosticCause(
                    title=c[0],
                    probability=c[1],
                    explanation=c[2]
                )
                for c in known["causes"]
            ]
            steps = known["steps"]

        telemetry: Dict[str, Any] = {"code": clean_code, "normalized_title": title}

        # Analyze Freeze-Frame telemetry if provided
        if request.freeze_frame:
            ff = request.freeze_frame
            telemetry["freeze_frame_submitted"] = True

            # Calculate total fuel trim if available
            if ff.short_term_fuel_trim_pct is not None and ff.long_term_fuel_trim_pct is not None:
                total_trim = ff.short_term_fuel_trim_pct + ff.long_term_fuel_trim_pct
                telemetry["total_fuel_trim_pct"] = round(total_trim, 1)

                if total_trim > 12.0:
                    telemetry["mixture_state"] = "LEAN MIXTURE DETECTED (Adding Fuel)"
                    if clean_code in ["P0300", "P0301"]:
                        for c in causes:
                            if "vacuum leak" in c.title.lower():
                                c.probability = min(100, c.probability + 20)
                elif total_trim < -10.0:
                    telemetry["mixture_state"] = "RICH MIXTURE DETECTED (Subtracting Fuel)"

            if ff.engine_coolant_temp_f is not None:
                telemetry["coolant_temp_f"] = ff.engine_coolant_temp_f
                if ff.engine_coolant_temp_f < 160:
                    telemetry["thermal_state"] = "ENGINE COLD (Possible Stuck Thermostat or Cold Start)"
                elif ff.engine_coolant_temp_f > 225:
                    telemetry["thermal_state"] = "OVERHEATING RISK DETECTED (>225°F)"
                    urgency = RiskLevel.CRITICAL
                    is_safe = False

            if ff.battery_voltage is not None:
                telemetry["battery_voltage"] = ff.battery_voltage
                if ff.battery_voltage < 12.0:
                    telemetry["electrical_warning"] = "Low system voltage detected; may trigger ghost communication DTCs."

        # Re-normalize cause probabilities to 100%
        total_prob = sum(c.probability for c in causes)
        if total_prob > 0:
            for c in causes:
                c.probability = int(round((c.probability / total_prob) * 100))

        cost = get_cost_estimate(repair_key, fallback_title=title)

        rag_chunks = []
        if request.include_rag_chunks:
            try:
                retriever = self._get_retriever()
                search_query = f"{clean_code} {title} diagnosis troubleshooting"
                rag_resp = retriever.search(query=search_query, top_k=3, similarity_threshold=0.20)
                for item in rag_resp.results:
                    rag_chunks.append({
                        "document_title": item.document_title,
                        "section": item.section,
                        "similarity": item.similarity,
                        "content": item.content[:400] + ("..." if len(item.content) > 400 else "")
                    })
            except Exception:
                pass

        return ProblemAnalysisResult(
            analyzer_id="dtc_code_analyzer",
            analyzer_title="OBD-II Diagnostic Trouble Code Analyzer",
            subsystem=subsystem,
            primary_verdict=f"DTC {clean_code}: {title}",
            urgency=urgency,
            is_safe_to_drive=is_safe,
            driving_advisory=driving_advisory,
            probable_causes=causes,
            action_plan=steps,
            cost_estimate=cost,
            telemetry_summary=telemetry,
            rag_reference_chunks=rag_chunks
        )
