"""
AutoAssist AI - Automotive Repair Cost, Labor & Difficulty Estimator
Provides realistic parts cost ranges, labor hours, difficulty scores, and tool requirements.
Costs are benchmarked in Indian Rupees (₹) with USD reference equivalents.
"""
from typing import Dict, Any, Optional
from backend.app.analyzers.base import CostEstimate, DifficultyLevel

# Database of standard automotive repairs with INR (₹) benchmarks
REPAIR_ESTIMATES: Dict[str, Dict[str, Any]] = {
    "battery_replacement": {
        "parts": "₹4,500 - ₹8,500",
        "parts_inr": "₹4,500 - ₹8,500",
        "parts_usd": "$90 - $180",
        "labor_hours": 0.5,
        "pro_total": "₹5,500 - ₹10,500",
        "pro_total_inr": "₹5,500 - ₹10,500",
        "pro_total_usd": "$140 - $260",
        "difficulty": DifficultyLevel.BEGINNER,
        "action": "Clean cable terminals with wire brush and replace 12V automotive battery.",
        "tools": ["10mm wrench or socket", "Battery terminal cleaner brush", "Dielectric grease", "Safety glasses"]
    },
    "alternator_replacement": {
        "parts": "₹7,500 - ₹18,000",
        "parts_inr": "₹7,500 - ₹18,000",
        "parts_usd": "$140 - $320",
        "labor_hours": 2.0,
        "pro_total": "₹11,000 - ₹24,000",
        "pro_total_inr": "₹11,000 - ₹24,000",
        "pro_total_usd": "$350 - $650",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Disconnect battery, release serpentine belt tensioner, unbolt alternator, and reconnect wiring harness.",
        "tools": ["Serpentine belt tensioner tool", "Socket set (10mm - 17mm)", "Digital multimeter", "Torque wrench"]
    },
    "starter_motor_replacement": {
        "parts": "₹5,500 - ₹14,000",
        "parts_inr": "₹5,500 - ₹14,000",
        "parts_usd": "$120 - $260",
        "labor_hours": 1.8,
        "pro_total": "₹8,000 - ₹18,000",
        "pro_total_inr": "₹8,000 - ₹18,000",
        "pro_total_usd": "$320 - $550",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Disconnect negative battery cable, raise vehicle on jack stands, unbolt starter motor and solenoid wiring.",
        "tools": ["Hydraulic jack and jack stands", "Ratchet and metric socket set", "Wire brush", "Multimeter"]
    },
    "parasitic_draw_repair": {
        "parts": "₹800 - ₹3,500",
        "parts_inr": "₹800 - ₹3,500",
        "parts_usd": "$15 - $80",
        "labor_hours": 1.5,
        "pro_total": "₹2,500 - ₹6,500",
        "pro_total_inr": "₹2,500 - ₹6,500",
        "pro_total_usd": "$180 - $320",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Perform millivolt drop fuse test or inline ammeter check to isolate parasitic circuit drain.",
        "tools": ["Digital multimeter with 10A fused DC jack", "Fuse puller", "Wiring schematic diagram"]
    },
    "thermostat_replacement": {
        "parts": "₹1,200 - ₹3,500",
        "parts_inr": "₹1,200 - ₹3,500",
        "parts_usd": "$25 - $60",
        "labor_hours": 1.5,
        "pro_total": "₹2,800 - ₹6,000",
        "pro_total_inr": "₹2,800 - ₹6,000",
        "pro_total_usd": "$180 - $320",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Drain partial coolant, remove thermostat housing, install new thermostat with spring facing engine block, bleed air.",
        "tools": ["Coolant drain pan", "10mm/12mm sockets", "Spill-free funnel", "50/50 ethylene glycol coolant"]
    },
    "water_pump_replacement": {
        "parts": "₹3,500 - ₹10,500",
        "parts_inr": "₹3,500 - ₹10,500",
        "parts_usd": "$60 - $180",
        "labor_hours": 3.0,
        "pro_total": "₹6,500 - ₹16,500",
        "pro_total_inr": "₹6,500 - ₹16,500",
        "pro_total_usd": "$450 - $850",
        "difficulty": DifficultyLevel.ADVANCED,
        "action": "Drain coolant, remove drive belts (and timing belt if water pump is timing driven), replace pump and gasket.",
        "tools": ["Coolant drain pan", "Torque wrench", "Gasket scraper", "Socket set", "Spill-free bleeding kit"]
    },
    "radiator_replacement": {
        "parts": "₹5,500 - ₹15,000",
        "parts_inr": "₹5,500 - ₹15,000",
        "parts_usd": "$110 - $280",
        "labor_hours": 2.5,
        "pro_total": "₹8,500 - ₹19,500",
        "pro_total_inr": "₹8,500 - ₹19,500",
        "pro_total_usd": "$380 - $700",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Drain cooling system, disconnect transmission cooler lines and radiator hoses, unbolt electric fan shroud, replace radiator.",
        "tools": ["Hose clamp pliers", "Flare nut wrench for transmission lines", "Drain pan", "Fresh coolant"]
    },
    "cooling_fan_motor_relay": {
        "parts": "₹1,500 - ₹5,500",
        "parts_inr": "₹1,500 - ₹5,500",
        "parts_usd": "$20 - $110",
        "labor_hours": 1.0,
        "pro_total": "₹2,500 - ₹7,500",
        "pro_total_inr": "₹2,500 - ₹7,500",
        "pro_total_usd": "$140 - $280",
        "difficulty": DifficultyLevel.BEGINNER,
        "action": "Test fan relay coil resistance and swap with identical horn/fog relay; replace fan assembly if motor draws high amps.",
        "tools": ["12V test light or multimeter", "Socket set", "Needle-nose pliers"]
    },
    "cylinder_head_gasket": {
        "parts": "₹8,000 - ₹24,000",
        "parts_inr": "₹8,000 - ₹24,000",
        "parts_usd": "$150 - $400",
        "labor_hours": 8.0,
        "pro_total": "₹25,000 - ₹60,000",
        "pro_total_inr": "₹25,000 - ₹60,000",
        "pro_total_usd": "$1400 - $2600",
        "difficulty": DifficultyLevel.PROFESSIONAL,
        "action": "Disassemble cylinder head, machine deck surface for flatness, install multi-layer steel (MLS) head gasket and torque-to-yield bolts.",
        "tools": ["Precision straightedge & feeler gauges", "Micrometer torque wrench & angle gauge", "Machine shop surfacing"]
    },
    "brake_pads_rotors_replacement": {
        "parts": "₹3,500 - ₹9,500",
        "parts_inr": "₹3,500 - ₹9,500",
        "parts_usd": "$80 - $190",
        "labor_hours": 1.8,
        "pro_total": "₹5,500 - ₹14,000",
        "pro_total_inr": "₹5,500 - ₹14,000",
        "pro_total_usd": "$280 - $550",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Remove wheel, unbolt caliper bracket, replace rotor, compress piston, lubricate slide pins with silicone brake grease.",
        "tools": ["Brake caliper piston compression tool", "14mm - 19mm sockets", "Brake cleaner", "Silicone ceramic grease"]
    },
    "brake_caliper_replacement": {
        "parts": "₹3,200 - ₹8,500",
        "parts_inr": "₹3,200 - ₹8,500",
        "parts_usd": "$70 - $160",
        "labor_hours": 1.5,
        "pro_total": "₹5,000 - ₹12,500",
        "pro_total_inr": "₹5,000 - ₹12,500",
        "pro_total_usd": "$260 - $450",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Clamp brake flex hose gently, unbolt banjo bolt, swap caliper, bleed hydraulic air using clean DOT 3/4 fluid.",
        "tools": ["Brake bleeder wrench (8mm/10mm)", "Catch bottle & clear tubing", "Brake fluid", "Torque wrench"]
    },
    "brake_master_cylinder": {
        "parts": "₹3,800 - ₹11,000",
        "parts_inr": "₹3,800 - ₹11,000",
        "parts_usd": "$80 - $220",
        "labor_hours": 2.0,
        "pro_total": "₹6,500 - ₹15,500",
        "pro_total_inr": "₹6,500 - ₹15,500",
        "pro_total_usd": "$320 - $600",
        "difficulty": DifficultyLevel.ADVANCED,
        "action": "Bench bleed new master cylinder to expel air bubbles before mounting to brake booster; bleed all four wheels.",
        "tools": ["Bench bleeding tube kit", "Flare nut wrenches (10mm/12mm)", "DOT 3/4 brake fluid"]
    },
    "spark_plugs_ignition_coils": {
        "parts": "₹2,500 - ₹9,500",
        "parts_inr": "₹2,500 - ₹9,500",
        "parts_usd": "$40 - $180",
        "labor_hours": 1.0,
        "pro_total": "₹3,800 - ₹12,500",
        "pro_total_inr": "₹3,800 - ₹12,500",
        "pro_total_usd": "$160 - $380",
        "difficulty": DifficultyLevel.BEGINNER,
        "action": "Disconnect electrical connectors, remove 10mm coil hold-down bolt, unscrew spark plug with 5/8 spark plug socket.",
        "tools": ["5/8 or 14mm spark plug socket with rubber insert", "Ratchet and extensions", "Spark plug gap gauge", "Dielectric grease"]
    },
    "maf_sensor_clean_or_replace": {
        "parts": "₹600 - ₹7,500",
        "parts_inr": "₹600 - ₹7,500",
        "parts_usd": "$12 - $180",
        "labor_hours": 0.5,
        "pro_total": "₹1,500 - ₹9,500",
        "pro_total_inr": "₹1,500 - ₹9,500",
        "pro_total_usd": "$110 - $280",
        "difficulty": DifficultyLevel.BEGINNER,
        "action": "Spray mass airflow sensor hot-wires thoroughly with dedicated CRC MAF Sensor Cleaner (do NOT touch wires); reinstall.",
        "tools": ["Phillips screwdriver or Torx security bit", "MAF cleaner spray aerosol"]
    },
    "vacuum_leak_repair": {
        "parts": "₹600 - ₹3,500",
        "parts_inr": "₹600 - ₹3,500",
        "parts_usd": "$10 - $60",
        "labor_hours": 1.5,
        "pro_total": "₹2,200 - ₹6,500",
        "pro_total_inr": "₹2,200 - ₹6,500",
        "pro_total_usd": "$180 - $350",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Perform smoke test into intake manifold, locate billowing smoke, replace cracked vacuum line or PCV hose.",
        "tools": ["Automotive smoke machine or propane torch (unlit) wand", "Hose cutter", "Pliers"]
    },
    "catalytic_converter": {
        "parts": "₹18,000 - ₹55,000",
        "parts_inr": "₹18,000 - ₹55,000",
        "parts_usd": "$350 - $1100",
        "labor_hours": 2.2,
        "pro_total": "₹24,000 - ₹68,000",
        "pro_total_inr": "₹24,000 - ₹68,000",
        "pro_total_usd": "$650 - $1600",
        "difficulty": DifficultyLevel.ADVANCED,
        "action": "Soak flange studs with penetrating oil, unbolt exhaust flanges, replace upstream/downstream gaskets and oxygen sensors.",
        "tools": ["Penetrating oil (PB Blaster)", "Oxygen sensor socket", "Impact wrench or long breaker bar", "New exhaust gaskets"]
    },
    "oxygen_sensor_replacement": {
        "parts": "₹2,800 - ₹8,500",
        "parts_inr": "₹2,800 - ₹8,500",
        "parts_usd": "$50 - $140",
        "labor_hours": 0.8,
        "pro_total": "₹4,200 - ₹11,500",
        "pro_total_inr": "₹4,200 - ₹11,500",
        "pro_total_usd": "$150 - $290",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Spray sensor threads while warm with penetrating oil, use slotted 7/8 (22mm) O2 sensor socket to remove, apply anti-seize to threads.",
        "tools": ["7/8 inch (22mm) slotted O2 sensor socket", "Breaker bar", "Thread anti-seize paste"]
    },
    "transmission_fluid_service": {
        "parts": "₹3,500 - ₹8,500",
        "parts_inr": "₹3,500 - ₹8,500",
        "parts_usd": "$50 - $120",
        "labor_hours": 1.2,
        "pro_total": "₹5,500 - ₹12,000",
        "pro_total_inr": "₹5,500 - ₹12,000",
        "pro_total_usd": "$180 - $320",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Drain transmission oil pan, replace internal Dacron/mesh filter and pan gasket, torque pan bolts to 90 in-lbs, refill to exact level.",
        "tools": ["Fluid drain pan", "Fluid transfer pump", "Inch-pound torque wrench", "OEM manufacturer ATF"]
    },
    "cv_axle_replacement": {
        "parts": "₹4,500 - ₹12,000",
        "parts_inr": "₹4,500 - ₹12,000",
        "parts_usd": "$90 - $190",
        "labor_hours": 2.0,
        "pro_total": "₹7,000 - ₹16,500",
        "pro_total_inr": "₹7,000 - ₹16,500",
        "pro_total_usd": "$320 - $550",
        "difficulty": DifficultyLevel.ADVANCED,
        "action": "Remove axle nut (32mm - 36mm), separate lower ball joint, pop inner tripod joint from transaxle with pry bar, install new half-shaft.",
        "tools": ["Axle nut socket (32mm/36mm)", "High-torque breaker bar or impact gun", "Pry bar", "Torque wrench (200 ft-lbs)"]
    },
    "wheel_bearing_hub_assembly": {
        "parts": "₹3,800 - ₹11,500",
        "parts_inr": "₹3,800 - ₹11,500",
        "parts_usd": "$80 - $210",
        "labor_hours": 2.0,
        "pro_total": "₹6,500 - ₹15,500",
        "pro_total_inr": "₹6,500 - ₹15,500",
        "pro_total_usd": "$320 - $580",
        "difficulty": DifficultyLevel.ADVANCED,
        "action": "Remove brake caliper and rotor, unbolt 4 hub bolts from behind steering knuckle, slide out old unit bearing, torque to spec.",
        "tools": ["Hub puller / slide hammer", "Torque wrench", "Wire brush", "Brake caliper hanger hook"]
    },
    "sway_bar_links_bushing": {
        "parts": "₹1,200 - ₹3,800",
        "parts_inr": "₹1,200 - ₹3,800",
        "parts_usd": "$35 - $85",
        "labor_hours": 1.0,
        "pro_total": "₹2,500 - ₹5,800",
        "pro_total_inr": "₹2,500 - ₹5,800",
        "pro_total_usd": "$140 - $250",
        "difficulty": DifficultyLevel.BEGINNER,
        "action": "Counter-hold inner ball joint pin with Allen key while turning locknut with box wrench; replace link rods and greased bushings.",
        "tools": ["Metric box wrenches", "Allen keys / hex sockets", "Penetrating oil"]
    },
    "ac_refrigerant_recharge_leak_repair": {
        "parts": "₹1,800 - ₹5,000",
        "parts_inr": "₹1,800 - ₹5,000",
        "parts_usd": "$40 - $150",
        "labor_hours": 1.5,
        "pro_total": "₹3,800 - ₹9,500",
        "pro_total_inr": "₹3,800 - ₹9,500",
        "pro_total_usd": "$220 - $420",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Locate leak with UV blacklight, evacuate remaining refrigerant with recovery machine, replace Schrader valve/O-ring, pull vacuum to 29 in-Hg, recharge exact weight.",
        "tools": ["HVAC manifold gauge set", "Rotary vane vacuum pump", "Refrigerant electronic scale", "UV inspection flashlight"]
    },
    "blend_door_actuator": {
        "parts": "₹1,500 - ₹4,500",
        "parts_inr": "₹1,500 - ₹4,500",
        "parts_usd": "$30 - $75",
        "labor_hours": 1.5,
        "pro_total": "₹3,200 - ₹7,500",
        "pro_total_inr": "₹3,200 - ₹7,500",
        "pro_total_usd": "$180 - $350",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "action": "Remove glovebox or lower hush panel, remove 3 small 5.5mm/7mm screws, unplug actuator wiring, clock gear and reinstall.",
        "tools": ["1/4-inch drive ratchet", "5.5mm / 7mm / 8mm sockets", "Trim removal tool"]
    }
}


def get_cost_estimate(repair_key: str, fallback_title: Optional[str] = None) -> CostEstimate:
    """Returns a standardized CostEstimate in INR (₹) with USD reference for a given repair."""
    data = REPAIR_ESTIMATES.get(repair_key)
    if not data:
        # Generic estimate fallback
        return CostEstimate(
            diy_parts_cost_range_inr="₹2,500 - ₹9,500",
            professional_labor_hours=1.5,
            professional_total_cost_range_inr="₹5,500 - ₹16,000",
            diy_parts_cost_range_usd="$40 - $150",
            professional_total_cost_range_usd="$180 - $350",
            difficulty=DifficultyLevel.INTERMEDIATE,
            recommended_action=f"Perform diagnostic inspection for {fallback_title or 'suspected component'}."
        )
    return CostEstimate(
        diy_parts_cost_range_inr=data.get("parts_inr", data.get("parts", "₹3,500 - ₹9,000")),
        professional_labor_hours=data["labor_hours"],
        professional_total_cost_range_inr=data.get("pro_total_inr", data.get("pro_total", "₹5,500 - ₹15,000")),
        diy_parts_cost_range_usd=data.get("parts_usd", "$50 - $150"),
        professional_total_cost_range_usd=data.get("pro_total_usd", "$150 - $350"),
        difficulty=data["difficulty"],
        recommended_action=data["action"],
    )
