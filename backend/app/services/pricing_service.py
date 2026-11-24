import logging
from typing import List, Optional, Dict, Any
from backend.app.config import settings
from backend.app.database import get_supabase_client
from backend.app.schemas.pricing import RepairPricingItem, RepairEstimateRequest, RepairEstimateResponse

logger = logging.getLogger(__name__)

# City hourly labor multipliers in India
CITY_LABOR_RATES: Dict[str, float] = {
    "all india": 600.0,
    "bengaluru": 750.0,
    "bangalore": 750.0,
    "mumbai": 800.0,
    "delhi": 750.0,
    "ncr": 750.0,
    "hyderabad": 650.0,
    "chennai": 650.0,
    "pune": 700.0,
    "kolkata": 600.0,
    "ahmedabad": 600.0,
}

# Standard Reference Catalog of Verified Automotive Parts & Repair Benchmarks
PRICING_CATALOG: List[Dict[str, Any]] = [
    {
        "item_key": "engine_oil_synthetic",
        "part_name": "Synthetic Engine Oil (3.5L - 4.5L)",
        "category": "Filters & Fluids",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata", "Mahindra", "Kia", "Volkswagen"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 1800.0,
        "part_price_max": 3200.0,
        "labor_hours_min": 0.5,
        "labor_hours_max": 0.8,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 150.0,
        "difficulty": "Beginner",
        "city": "All India",
        "currency": "INR",
        "source": "OEM API SP / ILSAC GF-6 Specifications",
        "description": "Full synthetic 0W-20 or 5W-30 motor oil change with new drain plug crush washer.",
        "keywords": ["oil", "engine oil", "synthetic oil", "mobil", "castrol", "lubricant", "service oil"]
    },
    {
        "item_key": "oil_filter_oem",
        "part_name": "Engine Oil Filter",
        "category": "Filters & Fluids",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata", "Mahindra", "Kia", "Volkswagen"],
        "compatible_models": ["All"],
        "year_min": 2000,
        "year_max": 2026,
        "part_price_min": 350.0,
        "part_price_max": 750.0,
        "labor_hours_min": 0.3,
        "labor_hours_max": 0.5,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 50.0,
        "difficulty": "Beginner",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Spin-on / Cartridge Filter",
        "description": "High-efficiency micro-pleated oil filter element.",
        "keywords": ["oil filter", "filter", "cartridge"]
    },
    {
        "item_key": "air_filter_engine",
        "part_name": "Engine Air Filter Element",
        "category": "Filters & Fluids",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2000,
        "year_max": 2026,
        "part_price_min": 450.0,
        "part_price_max": 1200.0,
        "labor_hours_min": 0.2,
        "labor_hours_max": 0.3,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 50.0,
        "difficulty": "Beginner",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Cellulose Pleated Filter",
        "description": "Intake air filter replacement to prevent MAF sensor contamination and maintain fuel economy.",
        "keywords": ["air filter", "engine air filter", "intake filter"]
    },
    {
        "item_key": "cabin_ac_filter",
        "part_name": "Cabin Air Filter (A/C)",
        "category": "Filters & Fluids",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 400.0,
        "part_price_max": 1100.0,
        "labor_hours_min": 0.2,
        "labor_hours_max": 0.4,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 50.0,
        "difficulty": "Beginner",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Activated Carbon Filter",
        "description": "HVAC cabin particulate filter replacement behind glove box.",
        "keywords": ["cabin filter", "ac filter", "air conditioner filter", "cabin air"]
    },
    {
        "item_key": "front_brake_pads",
        "part_name": "Front Brake Pads (Set of 4)",
        "category": "Brakes",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 1800.0,
        "part_price_max": 4200.0,
        "labor_hours_min": 1.0,
        "labor_hours_max": 1.5,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 200.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Ceramic Friction Material",
        "description": "Front axle disc brake pads renewal, slider pin lubrication, and hardware clips.",
        "keywords": ["brake pads", "front brake pads", "brake pad", "pads", "disc pads", "brake friction", "brake squeal"]
    },
    {
        "item_key": "rear_brake_pads_shoes",
        "part_name": "Rear Brake Pads / Shoes",
        "category": "Brakes",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 1400.0,
        "part_price_max": 3500.0,
        "labor_hours_min": 1.0,
        "labor_hours_max": 1.8,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 200.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Rear Brake Assemblies",
        "description": "Rear brake friction lining replacement with parking brake cable adjustment.",
        "keywords": ["rear brake pads", "brake shoes", "rear pads", "rear brakes", "drum shoes"]
    },
    {
        "item_key": "brake_rotor_front",
        "part_name": "Front Brake Rotor (Single)",
        "category": "Brakes",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 2200.0,
        "part_price_max": 4800.0,
        "labor_hours_min": 0.8,
        "labor_hours_max": 1.2,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 150.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "Vented Cast Iron Disc",
        "description": "Precision balanced brake disc rotor replacement to eliminate pedal vibration.",
        "keywords": ["brake rotor", "rotor", "brake disc", "disc rotor", "warped rotor"]
    },
    {
        "item_key": "brake_fluid_flush",
        "part_name": "DOT 4 Brake Fluid Flush",
        "category": "Brakes",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2000,
        "year_max": 2026,
        "part_price_min": 450.0,
        "part_price_max": 950.0,
        "labor_hours_min": 1.0,
        "labor_hours_max": 1.4,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 100.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "High-Boiling DOT 4 Glycol Fluid",
        "description": "Hydraulic bleed of master cylinder, ABS block, and 4 wheel calipers.",
        "keywords": ["brake fluid", "brake bleed", "fluid flush", "dot 4", "brake hydraulic"]
    },
    {
        "item_key": "automotive_battery_12v",
        "part_name": "12V Lead-Acid / AGM Battery (35Ah - 60Ah)",
        "category": "Electrical",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2000,
        "year_max": 2026,
        "part_price_min": 4500.0,
        "part_price_max": 8500.0,
        "labor_hours_min": 0.4,
        "labor_hours_max": 0.6,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 100.0,
        "difficulty": "Beginner",
        "city": "All India",
        "currency": "INR",
        "source": "Exide / Amaron / OEM 36-60 Month Warranty",
        "description": "Automotive 12V starting battery renewal with anti-corrosion terminal wash.",
        "keywords": ["battery", "car battery", "12v battery", "exide", "amaron", "dead battery", "starting battery"]
    },
    {
        "item_key": "alternator_assembly",
        "part_name": "Alternator Assembly (70A - 110A)",
        "category": "Electrical",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 7500.0,
        "part_price_max": 18000.0,
        "labor_hours_min": 1.5,
        "labor_hours_max": 2.5,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 300.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Rebuilt / New Unit",
        "description": "Alternator replacement with charging circuit verification and belt re-tensioning.",
        "keywords": ["alternator", "generator", "charging system", "battery not charging", "alternator whine"]
    },
    {
        "item_key": "starter_motor_assembly",
        "part_name": "Starter Motor Assembly",
        "category": "Electrical",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 5500.0,
        "part_price_max": 14000.0,
        "labor_hours_min": 1.5,
        "labor_hours_max": 2.0,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 250.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Gear Reduction Starter",
        "description": "Starter motor and solenoid replacement with ground connection test.",
        "keywords": ["starter", "starter motor", "cranking motor", "clicking starter", "no crank"]
    },
    {
        "item_key": "thermostat_housing_assembly",
        "part_name": "Thermostat & Gasket Assembly",
        "category": "Cooling",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 1200.0,
        "part_price_max": 3500.0,
        "labor_hours_min": 1.2,
        "labor_hours_max": 1.8,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 200.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Wax Pellet Thermostat",
        "description": "Thermostat renewal and thermal air bleed to restore coolant flow.",
        "keywords": ["thermostat", "thermostat valve", "overheating", "temperature regulator"]
    },
    {
        "item_key": "water_pump_replacement",
        "part_name": "Engine Water Pump & Gasket",
        "category": "Cooling",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 3500.0,
        "part_price_max": 10500.0,
        "labor_hours_min": 2.5,
        "labor_hours_max": 4.0,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 400.0,
        "difficulty": "Advanced",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Mechanical Impeller Pump",
        "description": "Coolant pump renewal to restore forced coolant circulation.",
        "keywords": ["water pump", "coolant pump", "pump impeller", "coolant leak water pump"]
    },
    {
        "item_key": "radiator_replacement",
        "part_name": "Aluminum Core Radiator",
        "category": "Cooling",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 5500.0,
        "part_price_max": 15000.0,
        "labor_hours_min": 2.0,
        "labor_hours_max": 3.0,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 350.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Brazed Aluminum Core",
        "description": "Radiator replacement, transmission cooler line reconnections, and fluid refill.",
        "keywords": ["radiator", "radiator core", "cracked radiator", "radiator leak"]
    },
    {
        "item_key": "spark_plugs_iridium",
        "part_name": "Iridium Spark Plugs (Set of 4)",
        "category": "Engine",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 1600.0,
        "part_price_max": 3800.0,
        "labor_hours_min": 0.8,
        "labor_hours_max": 1.2,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 100.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "Laser Iridium / Platinum Plugs",
        "description": "Spark plug replacement torqued to specification (18-22 Nm) to eliminate misfires.",
        "keywords": ["spark plugs", "spark plug", "plugs", "ignition plugs", "misfire plugs", "iridium"]
    },
    {
        "item_key": "ignition_coil_pack",
        "part_name": "Ignition Coil Pack (Single)",
        "category": "Engine",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 1800.0,
        "part_price_max": 4500.0,
        "labor_hours_min": 0.4,
        "labor_hours_max": 0.6,
        "labor_rate_hourly": 600.0,
        "additional_expenses_estimate": 50.0,
        "difficulty": "Beginner",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Direct Coil On Plug (COP)",
        "description": "Coil replacement with dielectric boot grease for cylinder misfire recovery.",
        "keywords": ["ignition coil", "coil pack", "coil", "cop coil", "misfire coil"]
    },
    {
        "item_key": "clutch_disc_pressure_plate_set",
        "part_name": "Clutch Disc & Pressure Plate Kit",
        "category": "Transmission",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 4500.0,
        "part_price_max": 11500.0,
        "labor_hours_min": 4.0,
        "labor_hours_max": 6.0,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 500.0,
        "difficulty": "Advanced",
        "city": "All India",
        "currency": "INR",
        "source": "OEM Valeo / Exedy / Sachs Friction Kit",
        "description": "Transmission drop, flywheel inspection, clutch disc, pressure plate, and release bearing.",
        "keywords": ["clutch", "clutch plate", "clutch disc", "clutch set", "slipping clutch", "pressure plate"]
    },
    {
        "item_key": "wheel_bearing_hub_assembly",
        "part_name": "Front Wheel Hub & Bearing Assembly",
        "category": "Suspension",
        "compatible_makes": ["Generic", "Honda", "Toyota", "Ford", "Maruti", "Hyundai", "Tata"],
        "compatible_models": ["All"],
        "year_min": 2005,
        "year_max": 2026,
        "part_price_min": 2200.0,
        "part_price_max": 5500.0,
        "labor_hours_min": 1.5,
        "labor_hours_max": 2.5,
        "labor_rate_hourly": 650.0,
        "additional_expenses_estimate": 250.0,
        "difficulty": "Intermediate",
        "city": "All India",
        "currency": "INR",
        "source": "Sealed Hub Bearing (SKF/FAG/OEM)",
        "description": "Wheel hub bearing replacement to eliminate humming and roaring noises at road speed.",
        "keywords": ["wheel bearing", "bearing", "hub bearing", "wheel hub", "bearing noise"]
    }
]


class PricingService:
    def __init__(self):
        self._supabase = None
        self._items = PRICING_CATALOG
        self._init_client()

    def _init_client(self):
        if settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key):
            try:
                self._supabase = get_supabase_client(admin=True)
                res = self._supabase.table("repair_pricing").select("*").execute()
                if res.data and len(res.data) > 0:
                    logger.info("PricingService: Loaded %d benchmark records from Supabase.", len(res.data))
                    for row in res.data:
                        if not row.get("keywords"):
                            row["keywords"] = [row["part_name"].lower()]
                    self._items = res.data
            except Exception as e:
                logger.warning("PricingService: Supabase query failed (%s). Using reference catalog.", e)

    def _get_labor_rate(self, city: Optional[str] = None) -> float:
        """Returns the hourly labor rate in INR for the requested city or fallback."""
        if not city:
            return 650.0
        city_lower = city.lower().strip()
        return CITY_LABOR_RATES.get(city_lower, 650.0)

    def list_catalog(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if category:
            cat_lower = category.lower()
            return [it for it in self._items if it["category"].lower() == cat_lower]
        return self._items

    def find_matching_item(self, text: str) -> Optional[Dict[str, Any]]:
        text_lower = text.lower().strip()
        # Direct key match
        for it in self._items:
            if it["item_key"] == text_lower or it["part_name"].lower() == text_lower:
                return it

        # Keyword match
        for it in self._items:
            for kw in it.get("keywords", []):
                if kw in text_lower:
                    return it

        # Partial token match
        tokens = text_lower.split()
        best_match = None
        max_matches = 0
        for it in self._items:
            score = 0
            name_words = it["part_name"].lower().split()
            for t in tokens:
                if len(t) > 2 and any(t in w for w in name_words):
                    score += 1
            if score > max_matches:
                max_matches = score
                best_match = it

        return best_match if max_matches > 0 else None

    def estimate_repair_cost(self, req: RepairEstimateRequest) -> RepairEstimateResponse:
        item = self.find_matching_item(req.issue_or_part)
        city_lower = (req.city or "All India").lower().strip()
        labor_rate = CITY_LABOR_RATES.get(city_lower, 650.0)

        make_str = req.make or "Generic"
        model_str = req.model or "All"
        vehicle_display = f"{make_str} {model_str}".strip()

        if not item:
            # Explicitly return data unavailable as instructed in Part 5
            return RepairEstimateResponse(
                query=req.issue_or_part,
                matched=False,
                part_name="Pricing data unavailable",
                category="General",
                vehicle_applied=vehicle_display,
                city_applied=req.city or "All India",
                parts_cost_range_inr="Pricing data unavailable",
                parts_cost_min=0.0,
                parts_cost_max=0.0,
                labor_hours=0.0,
                labor_charge_inr="Pricing data unavailable",
                labor_charge_min=0.0,
                labor_charge_max=0.0,
                additional_expenses_inr="₹0",
                additional_expenses=0.0,
                total_estimated_cost_inr="Pricing data unavailable",
                total_min=0.0,
                total_max=0.0,
                difficulty="Unknown",
                pricing_source="No verified market pricing record found for this query",
                disclaimer=(
                    "Pricing data unavailable for this specific component. "
                    "AutoAssist AI does not generate fictitious prices. "
                    "Please consult a certified garage for a bespoke quotation."
                )
            )

        # Calculate with vehicle / city context
        parts_min = item["part_price_min"]
        parts_max = item["part_price_max"]
        hours_avg = round((item["labor_hours_min"] + item["labor_hours_max"]) / 2, 1)
        labor_min = round(item["labor_hours_min"] * labor_rate, 2)
        labor_max = round(item["labor_hours_max"] * labor_rate, 2)
        additional = item["additional_expenses_estimate"]

        total_min = round(parts_min + labor_min + additional, 2)
        total_max = round(parts_max + labor_max + additional, 2)

        return RepairEstimateResponse(
            query=req.issue_or_part,
            matched=True,
            part_name=item["part_name"],
            category=item["category"],
            vehicle_applied=vehicle_display,
            city_applied=req.city or "All India",
            parts_cost_range_inr=f"₹{int(parts_min):,} - ₹{int(parts_max):,}",
            parts_cost_min=parts_min,
            parts_cost_max=parts_max,
            labor_hours=hours_avg,
            labor_charge_inr=f"₹{int(labor_min):,} - ₹{int(labor_max):,}",
            labor_charge_min=labor_min,
            labor_charge_max=labor_max,
            additional_expenses_inr=f"₹{int(additional):,}",
            additional_expenses=additional,
            total_estimated_cost_inr=f"₹{int(total_min):,} - ₹{int(total_max):,}",
            total_min=total_min,
            total_max=total_max,
            difficulty=item["difficulty"],
            pricing_source=item["source"]
        )


_pricing_service_instance = None


def get_pricing_service() -> PricingService:
    global _pricing_service_instance
    if _pricing_service_instance is None:
        _pricing_service_instance = PricingService()
    return _pricing_service_instance
