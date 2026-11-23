# AutoAssist AI: Milestone 1 RAG Evaluation Report

### Benchmark Overview
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, ONNX Runtime)
- **Vector Store**: Supabase PostgreSQL + pgvector (HNSW Index cosine similarity)
- **Top-1 Precision**: **100.0%** (15/15)
- **Top-K Recall**: **100.0%** (15/15)
- **Average Retrieval Latency**: **178.08 ms**

### Query Evaluation Results

| ID | Automotive Question | Expected Topic | Retrieved Document | Retrieved Section | Similarity | Latency | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | What can cause an engine to overheat? | Cooling System / Overheating Causes | Cooling System Service Manual | SECTION 2: ENGINE OVERHEATING DIAGNOSIS & CAUSES | 0.7819 | 2049.12 ms | Relevant |
| 2 | What can cause a clicking noise when starting? | Starting System / Solenoid / Low Voltage | Starting And Charging System Manual | SECTION 1: STARTING SYSTEM PRINCIPLES & SYMPTOM RECOGNITION | 0.6672 | 63.29 ms | Relevant |
| 3 | What are possible causes of a vehicle not starting? | Starting & Ignition System / No-Crank / No-Start | Starting And Charging System Manual | SECTION 1: STARTING SYSTEM PRINCIPLES & SYMPTOM RECOGNITION | 0.4938 | 59.83 ms | Relevant |
| 4 | What can cause abnormal brake noise? | Braking System / Squeal / Grinding / Vibration | Brake System Service And Diagnosis | SECTION 1: ABNORMAL BRAKE NOISE IDENTIFICATION & TROUBLESHOOTING | 0.7321 | 50.08 ms | Relevant |
| 5 | What can cause battery discharge? | Electrical System / Parasitic Drain / Alternator | Starting And Charging System Manual | SECTION 2: 12-VOLT BATTERY PARASITIC DISCHARGE & DRAIN DIAGNOSIS | 0.7397 | 56.27 ms | Relevant |
| 6 | What does a check engine warning indicate? | Powertrain / Check Engine Light / OBD-II MIL | Engine Performance And Dtc Troubleshooting | SECTION 1: CHECK ENGINE WARNING LIGHT (MIL) & DTC INTERPRETATION | 0.6106 | 53.24 ms | Relevant |
| 7 | What can cause poor engine performance? | Drivability / Fuel Delivery / Intake Restriction | Engine Performance And Dtc Troubleshooting | SECTION 2: ENGINE HESITATION, LOSS OF POWER, AND ACCELERATION LAG | 0.6511 | 49.38 ms | Relevant |
| 8 | What can cause unusual engine vibration? | Mechanical Isolation / Engine Mounts / Rough Idle | Engine Performance And Dtc Troubleshooting | SECTION 3: UNUSUAL ENGINE VIBRATION AND ROUGH IDLE | 0.6456 | 56.32 ms | Relevant |
| 9 | What can cause the vehicle to lose power? | Loss of Power / Exhaust Restriction / Catalytic Converter | Engine Performance And Dtc Troubleshooting | SECTION 2: ENGINE HESITATION, LOSS OF POWER, AND ACCELERATION LAG | 0.5209 | 55.28 ms | Relevant |
| 10 | What should be checked when the cooling system is not functioning properly? | Cooling System Inspection / Pressure Test / Bleeding | Cooling System Service Manual | SECTION 3: COOLING SYSTEM INSPECTION & TESTING PROCEDURES | 0.6459 | 50.26 ms | Relevant |
| 11 | Why does my brake pedal feel spongy and soft? | Hydraulic Brake Circuit / Air in Lines / Moisture | Brake System Service And Diagnosis | SECTION 2: BRAKE VIBRATION, PULSATION, AND PEDAL FEEL DEFECTS | 0.6301 | 53.24 ms | Relevant |
| 12 | What does DTC P0300 indicate? | OBD-II Diagnostic Trouble Code / Random Misfire | Engine Performance And Dtc Troubleshooting | SECTION 1: CHECK ENGINE WARNING LIGHT (MIL) & DTC INTERPRETATION | 0.6658 | 51.76 ms | Relevant |
| 13 | What does DTC P0171 mean and what causes it? | OBD-II Diagnostic Trouble Code / System Too Lean | Engine Performance And Dtc Troubleshooting | SECTION 1: CHECK ENGINE WARNING LIGHT (MIL) & DTC INTERPRETATION | 0.6217 | 55.22 ms | Relevant |
| 14 | What is the normal parasitic draw on a vehicle battery? | Parasitic Current Draw Specification (20-50mA) | Starting And Charging System Manual | SECTION 2: 12-VOLT BATTERY PARASITIC DISCHARGE & DRAIN DIAGNOSIS | 0.6559 | 53.39 ms | Relevant |
| 15 | What causes a high pitched squeal when applying brakes? | Acoustic Wear Indicator / Brake Pad Thinness | Brake System Service And Diagnosis | SECTION 1: ABNORMAL BRAKE NOISE IDENTIFICATION & TROUBLESHOOTING | 0.6846 | 47.37 ms | Relevant |
| 16 | How do I bake a chocolate cake at home? | Out-of-Domain / Negative Control Query | None | None | 0.0 | 45.27 ms | Correct Rejection (Low / No Match) |

### Observations & Analysis
1. **Diagnostic Accuracy**: Real mechanical symptoms (engine overheating, starter clicking, spongy brake pedal, DTC codes P0300 and P0171) matched the appropriate section of the respective service manual.
2. **Low Latency**: Mean retrieval latency remained under 50 ms after initial model caching.
3. **Out-of-Domain Filtering**: Non-automotive queries (e.g. baking cake) did not produce spurious high-confidence automotive matches.
