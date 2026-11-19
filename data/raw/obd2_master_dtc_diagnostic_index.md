# OBD-II MASTER DIAGNOSTIC TROUBLE CODE (DTC) REFERENCE INDEX
Document Type: Diagnostic Guide
Manufacturer: SAE Standard / Generic / OBD-II Compliant
Vehicle Model: All OBD-II Vehicles (1996 - Present)
Model Year: 2024
Source: Society of Automotive Engineers (SAE J2012) / ISO 15031-6
Source URL: https://www.sae.org/standards/content/j2012_201612/

<!-- PAGE 1 -->
## SECTION 1: OBD-II CODE STRUCTURE & ARCHITECTURE

Standard Diagnostic Trouble Codes (DTCs) consist of 5 alphanumeric characters:
- 1st Character: System Domain:
  - 'P' = Powertrain (Engine, Transmission, Emissions)
  - 'B' = Body (Airbags, Climate, Lighting, Instruments)
  - 'C' = Chassis (ABS, Traction Control, Steering, Suspension)
  - 'U' = Network Communication (CAN Bus, Modules communication)
- 2nd Character: Code Type:
  - '0' = Standard SAE Generic Code
  - '1' = Manufacturer-Specific Code
- 3rd Character: Subsystem:
  - '1' or '2' = Fuel and Air Metering
  - '3' = Ignition System or Engine Misfire
  - '4' = Auxiliary Emissions Controls (EVAP, Cat, EGR)
  - '5' = Vehicle Speed & Idle Control System
  - '6' = Computer & Output Circuit
  - '7', '8', '9' = Transmission Controls

<!-- PAGE 2 -->
## SECTION 2: TOP ENGINE POWERTRAIN (P-CODES) & DIAGNOSTIC WORKFLOWS

### P0300 - Random / Multiple Cylinder Misfire Detected
- Meaning: Powertrain Control Module (PCM) detected crankshaft acceleration drops across multiple cylinders.
- Freeze Frame Clues: If Fuel Trim (LTFT) is high (> +15%), misfire is caused by lean fuel mixture or vacuum leak. If LTFT is negative (< -10%), misfire is rich (fuel dripping, stuck injector, ignition failure).
- Common Causes: Worn spark plugs, failing ignition coil packs, low fuel pressure, intake manifold vacuum leak, EGR stuck open, low cylinder compression.
- Diagnostic Steps:
  1. Inspect spark plugs for fouling, oil contamination, or excessive gap (>0.044 inch).
  2. Swap suspected ignition coils to different cylinders: if misfire moves to the new cylinder (e.g., P0301 moves to P0303), the coil is defective.
  3. Perform smoke test on intake manifold for unmetered air leaks.

### P0171 / P0174 - System Too Lean (Bank 1 / Bank 2)
- Meaning: PCM is adding more than 20% to 25% extra fuel (positive Long Term Fuel Trim) because oxygen sensor reports excess oxygen in exhaust.
- Diagnosis:
  1. Check LTFT at idle vs 2,500 RPM:
     - If LTFT is high (+20%) at idle but drops to normal (+5%) at 2,500 RPM, it is a VACUUM LEAK (cracked PCV hose, intake gasket, brake booster hose).
     - If LTFT remains high (+20%) at both idle and 2,500 RPM, it is a FUEL DELIVERY or AIR METERING problem (dirty MAF sensor, weak fuel pump, clogged fuel filter).
  2. Clean Mass Airflow (MAF) sensor hot wire with dedicated MAF cleaner spray.

### P0420 / P0430 - Catalyst System Efficiency Below Threshold (Bank 1 / Bank 2)
- Meaning: Downstream (post-cat) O2 sensor waveform mimics upstream (pre-cat) O2 sensor, indicating the catalytic converter substrate has lost its oxygen storage capacity.
- Common Misdiagnosis: DO NOT immediately replace the downstream O2 sensor! The O2 sensor is working correctly by reporting catalyst failure.
- Verify: Ensure there are no upstream exhaust leaks before the cat, no misfires (unburned fuel melts catalytic honeycomb), and engine is not burning excessive oil.

### P0128 - Coolant Thermostat (Coolant Temp Below Regulating Temperature)
- Meaning: Engine takes too long to warm up to target operating temperature (typically 176°F / 80°C within 15 minutes of driving).
- Cause: Thermostat stuck open or weak spring, allowing continuous coolant circulation to radiator.
- Remedy: Replace engine thermostat and rubber seal gasket; bleed air from cooling system.

### P0442 / P0455 - Evaporative Emission (EVAP) Control System Leak (Small / Large)
- Meaning: Fuel vapor recovery system failed vacuum decay test.
- Common Causes: Loose or damaged fuel filler cap (causes >60% of P0455 codes), cracked charcoal canister vent line, stuck open EVAP purge solenoid.
- Diagnostic: Tighten or replace gas cap, clear code, drive for 2 drive cycles. If code returns, introduce smoke machine test into EVAP service port.

<!-- PAGE 3 -->
## SECTION 3: CHASSIS (C-CODES) & NETWORK (U-CODES)

### C0035 / C0040 - Left / Right Front Wheel Speed Sensor Circuit
- Meaning: ABS control module lost pulse signal from tone ring (reluctor ring) on wheel hub.
- Symptoms: ABS Warning Light ON, Traction Control Disabled, pulsates at low speed stopping.
- Test: Measure wheel speed sensor resistance with multimeter (typically 1.0k to 1.5k ohms for passive magnetic sensors; active hall-effect sensors require 12V supply and oscilloscope pulse check). Check tone ring for cracked teeth or debris.

### U0100 - Lost Communication with ECM / PCM
- Meaning: Controller Area Network (CAN High / CAN Low) data bus lost packets from engine computer.
- Diagnostic: Measure CAN Bus termination resistance at OBD-II port between Pin 6 (CAN-H) and Pin 14 (CAN-L) with battery disconnected. Normal resistance is exactly 60 Ohms (two 120-Ohm resistors in parallel). If resistance measures 120 Ohms, one terminating resistor or bus wire is open. If resistance measures 0 Ohms, CAN lines are shorted together.
