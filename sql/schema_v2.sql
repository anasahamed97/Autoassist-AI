-- ==============================================================================
-- AutoAssist AI: Supabase PostgreSQL Extended Schema Migration (v2.0)
-- Adds Vehicles, Structured Pricing Database, Mechanic Quotations, & Maintenance
-- ==============================================================================

-- 1. VEHICLE PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default_user',
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    fuel_type TEXT NOT NULL DEFAULT 'Petrol',
    engine_variant TEXT,
    nickname TEXT,
    odometer INTEGER NOT NULL DEFAULT 45000,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_vehicles_user_id ON public.vehicles(user_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_make_model ON public.vehicles(make, model);

-- 2. STRUCTURED REPAIR PRICING DATABASE
CREATE TABLE IF NOT EXISTS public.repair_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_name TEXT NOT NULL,
    item_key TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    compatible_makes TEXT[] DEFAULT ARRAY['Generic']::TEXT[],
    compatible_models TEXT[] DEFAULT ARRAY['All']::TEXT[],
    year_min INTEGER DEFAULT 2000,
    year_max INTEGER DEFAULT 2026,
    part_price_min NUMERIC NOT NULL,
    part_price_max NUMERIC NOT NULL,
    labor_hours_min NUMERIC NOT NULL,
    labor_hours_max NUMERIC NOT NULL,
    labor_rate_hourly NUMERIC NOT NULL DEFAULT 600.0,
    additional_expenses_estimate NUMERIC NOT NULL DEFAULT 250.0,
    difficulty TEXT NOT NULL DEFAULT 'Intermediate',
    city TEXT NOT NULL DEFAULT 'All India',
    currency TEXT NOT NULL DEFAULT 'INR',
    source TEXT NOT NULL DEFAULT 'OEM Benchmark & Automotive Service Standards',
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_repair_pricing_category ON public.repair_pricing(category);
CREATE INDEX IF NOT EXISTS idx_repair_pricing_item_key ON public.repair_pricing(item_key);
CREATE INDEX IF NOT EXISTS idx_repair_pricing_part_name ON public.repair_pricing(part_name);

-- 3. MECHANIC QUOTATION COMPARISON RECORDS
CREATE TABLE IF NOT EXISTS public.mechanic_quotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default_user',
    vehicle_id UUID REFERENCES public.vehicles(id) ON DELETE SET NULL,
    repair_title TEXT NOT NULL,
    garage_name TEXT,
    quote_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_quoted NUMERIC NOT NULL,
    total_reference_min NUMERIC NOT NULL,
    total_reference_max NUMERIC NOT NULL,
    overall_status TEXT NOT NULL, -- 'Within reference range', 'Above reference range', 'Below reference range', 'Insufficient pricing data'
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    suggested_questions JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_quotations_user_id ON public.mechanic_quotations(user_id);
CREATE INDEX IF NOT EXISTS idx_quotations_vehicle_id ON public.mechanic_quotations(vehicle_id);

-- 4. VEHICLE MAINTENANCE REMINDERS & SERVICE LOGS
CREATE TABLE IF NOT EXISTS public.maintenance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default_user',
    vehicle_id UUID NOT NULL REFERENCES public.vehicles(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL,
    interval_months INTEGER NOT NULL DEFAULT 6,
    interval_km INTEGER NOT NULL DEFAULT 10000,
    last_service_date DATE,
    last_service_odometer INTEGER,
    next_due_date DATE,
    next_due_odometer INTEGER,
    status TEXT NOT NULL DEFAULT 'upcoming', -- 'upcoming', 'due_soon', 'overdue', 'completed'
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_maintenance_vehicle_id ON public.maintenance_records(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_status ON public.maintenance_records(status);

-- 5. INITIAL REPAIR PRICING BENCHMARK SEED DATA (INR ₹)
INSERT INTO public.repair_pricing (
    item_key, part_name, category, compatible_makes, compatible_models,
    part_price_min, part_price_max, labor_hours_min, labor_hours_max,
    labor_rate_hourly, additional_expenses_estimate, difficulty, city, source, description
) VALUES
('engine_oil_synthetic', 'Synthetic Engine Oil (3.5L - 4.5L)', 'Filters & Fluids', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1800, 3200, 0.5, 0.8, 600, 150, 'Beginner', 'All India', 'OEM Standard API SP / ILSAC GF-6', 'Full synthetic 0W-20 or 5W-30 engine oil change with drain plug crush washer.'),
('oil_filter_oem', 'Engine Oil Filter', 'Filters & Fluids', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 350, 750, 0.3, 0.5, 600, 50, 'Beginner', 'All India', 'OEM Spin-on / Cartridge Filter', 'High-efficiency cellulose / synthetic media oil filter element.'),
('air_filter_engine', 'Engine Air Filter Element', 'Filters & Fluids', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 450, 1200, 0.2, 0.3, 600, 50, 'Beginner', 'All India', 'OEM Pleated Paper Filter', 'Intake air cleaner element replacement to maintain stoichiometric fuel trim.'),
('cabin_ac_filter', 'Cabin Air (A/C) Filter', 'Filters & Fluids', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 400, 1100, 0.2, 0.4, 600, 50, 'Beginner', 'All India', 'Activated Carbon Particulate Filter', 'Pollen and particulate cabin air filter replacement behind dashboard glovebox.'),
('front_brake_pads', 'Front Brake Pads (Set of 4)', 'Brakes', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1800, 4200, 1.0, 1.5, 650, 200, 'Intermediate', 'All India', 'OEM Ceramic / Semi-Metallic Pads', 'Disc brake friction pads replacement including caliper slide pin cleaning and brake hardware.'),
('rear_brake_pads_shoes', 'Rear Brake Pads / Shoes', 'Brakes', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1400, 3500, 1.0, 1.8, 650, 200, 'Intermediate', 'All India', 'OEM Friction Lining', 'Rear axle brake friction material renewal with caliper reset or drum adjuster setting.'),
('brake_rotor_front', 'Front Brake Rotor (Single)', 'Brakes', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 2200, 4800, 0.8, 1.2, 650, 150, 'Intermediate', 'All India', 'Vented Cast Iron Disc', 'Precision balanced brake rotor replacement to eliminate pedal shudder and runout.'),
('brake_fluid_flush', 'DOT 4 Brake Fluid Flush', 'Brakes', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 450, 950, 1.0, 1.4, 650, 100, 'Intermediate', 'All India', 'High-Boiling DOT 4 Glycol Fluid', 'Complete hydraulic pressure bleed of brake calipers and ABS hydraulic unit.'),
('spark_plugs_iridium', 'Iridium Spark Plugs (Set of 4)', 'Engine', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1600, 3800, 0.8, 1.2, 600, 100, 'Intermediate', 'All India', 'OEM Laser Iridium / Platinum Plugs', 'Long-life spark plug renewal torqued to manufacturer specification (18-22 Nm).'),
('ignition_coil_pack', 'Ignition Coil Pack (Single)', 'Engine', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1800, 4500, 0.4, 0.6, 600, 50, 'Beginner', 'All India', 'OEM Direct Ignition (COP)', 'Electronic ignition coil pack renewal with dielectric silicone boot grease.'),
('automotive_battery_12v', '12V Lead-Acid / AGM Battery (35Ah - 60Ah)', 'Electrical', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 4500, 8500, 0.4, 0.6, 600, 100, 'Beginner', 'All India', 'Exide / Amaron / OEM 36-60 Month Warranty', 'Automotive SLI battery renewal with post corrosion cleanup and terminal protection.'),
('alternator_assembly', 'Alternator Assembly (70A - 110A)', 'Electrical', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 7500, 18000, 1.5, 2.5, 650, 300, 'Intermediate', 'All India', 'Denso / Bosch / OEM Rebuilt Unit', 'Alternator replacement including voltage regulator test and belt re-tensioning.'),
('starter_motor_assembly', 'Starter Motor Assembly', 'Electrical', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 5500, 14000, 1.5, 2.0, 650, 250, 'Intermediate', 'All India', 'OEM Gear-Reduction Starter', 'Cranking motor replacement with solenoid terminal check and ground cleaning.'),
('engine_coolant_flush', 'Ethylene Glycol Coolant (5L)', 'Cooling', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 800, 1800, 1.0, 1.5, 600, 150, 'Intermediate', 'All India', 'OEM 50/50 Pre-Mixed OAT Coolant', 'Complete cooling system drain, fresh fill, and spill-free thermal air purge.'),
('thermostat_housing_assembly', 'Thermostat & Seal Assembly', 'Cooling', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1200, 3500, 1.2, 1.8, 600, 200, 'Intermediate', 'All India', 'Wax-Pellet Thermostat (82C - 88C)', 'Thermostat replacement to prevent overcooling or thermal overheating.'),
('radiator_cooling_fan_motor', 'Radiator Electric Cooling Fan Motor', 'Cooling', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 2200, 5800, 1.0, 1.5, 600, 200, 'Intermediate', 'All India', 'OEM Dual-Speed Fan Motor', 'Fan shroud removal, motor renewal, and relay circuit activation test.'),
('clutch_disc_pressure_plate_set', 'Clutch Plate & Pressure Plate Kit', 'Transmission', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 4500, 11500, 4.0, 6.0, 650, 500, 'Advanced', 'All India', 'OEM Valeo / Exedy / Sachs Friction Kit', 'Transmission drop, flywheel inspection, clutch disc, pressure plate, and release bearing renewal.'),
('transmission_fluid_service', 'Transmission Fluid (ATF / CVT / MTF 3L - 4L)', 'Transmission', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 1500, 4500, 0.8, 1.5, 600, 150, 'Intermediate', 'All India', 'OEM Ultra HCF-2 / ATF-WS / MTF Fluid', 'Drain and refill transmission fluid to manufacturer exact level hashmarks.'),
('wheel_bearing_hub_assembly', 'Front Wheel Hub & Bearing Assembly', 'Suspension', ARRAY['Generic', 'Honda', 'Toyota', 'Ford', 'Maruti', 'Hyundai', 'Tata'], ARRAY['All'], 2200, 5500, 1.5, 2.5, 650, 250, 'Intermediate', 'All India', 'Precision Sealed Bearing Hub (SKF/FAG)', 'Wheel hub replacement to resolve road rumble and bearing noise.')
ON CONFLICT (item_key) DO UPDATE SET
    part_price_min = EXCLUDED.part_price_min,
    part_price_max = EXCLUDED.part_price_max,
    labor_hours_min = EXCLUDED.labor_hours_min,
    labor_hours_max = EXCLUDED.labor_hours_max,
    updated_at = timezone('utc'::text, now());
