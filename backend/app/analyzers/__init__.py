"""
AutoAssist AI - Problem Analyzers Package
Exports all dedicated automotive subsystem problem analyzers.
"""
from typing import List, Dict, Any

from backend.app.analyzers.base import (
    ProblemAnalysisResult,
    DiagnosticCause,
    ActionStep,
    RiskLevel,
    DifficultyLevel,
    CostEstimate
)
from backend.app.analyzers.dtc_analyzer import DTCProblemAnalyzer, DTCAnalysisRequest, FreezeFrameInput
from backend.app.analyzers.electrical_analyzer import ElectricalProblemAnalyzer, ElectricalAnalysisRequest
from backend.app.analyzers.thermal_analyzer import ThermalProblemAnalyzer, ThermalAnalysisRequest
from backend.app.analyzers.acoustic_analyzer import AcousticProblemAnalyzer, AcousticAnalysisRequest
from backend.app.analyzers.brake_analyzer import BrakeProblemAnalyzer, BrakeAnalysisRequest
from backend.app.analyzers.drivetrain_analyzer import DrivetrainProblemAnalyzer, DrivetrainAnalysisRequest
from backend.app.analyzers.emissions_analyzer import EmissionsProblemAnalyzer, EmissionsAnalysisRequest
from backend.app.analyzers.wizard_engine import GuidedWizardEngine, WizardStartRequest, WizardStepRequest
from backend.app.analyzers.cost_estimator import get_cost_estimate, REPAIR_ESTIMATES


def get_analyzer_catalog() -> List[Dict[str, Any]]:
    """Returns directory of all available problem analyzers with metadata and capability descriptions."""
    return [
        {
            "id": "dtc_code_analyzer",
            "name": "OBD-II Diagnostic Trouble Code (DTC) Scanner",
            "subsystem": "Powertrain & Electronic Control",
            "description": "Decodes Powertrain (P), Chassis (C), Body (B), and Network (U) codes with freeze-frame sensor interpretation.",
            "endpoint": "POST /api/analyzers/dtc",
            "icon": "chip",
            "sample_query": "P0300 (Random Misfire) or P0171 (System Lean)"
        },
        {
            "id": "electrical_multimeter_analyzer",
            "name": "Starting, Charging & Multimeter Analyzer",
            "subsystem": "12V Electrical & Battery",
            "description": "Calculates battery State-of-Charge (SoC%), starter cranking voltage drop, alternator regulation, and parasitic drain.",
            "endpoint": "POST /api/analyzers/electrical",
            "icon": "zap",
            "sample_query": "Resting: 12.2V, Cranking: 9.1V, Alternator: 13.9V"
        },
        {
            "id": "thermal_cooling_analyzer",
            "name": "Engine Overheating & Thermal Analyzer",
            "subsystem": "Cooling System & Thermostat",
            "description": "Diagnoses overheating triggers: idle vs highway, fan failure, thermostat, water pump impeller, airlock, and head gasket.",
            "endpoint": "POST /api/analyzers/thermal",
            "icon": "thermometer",
            "sample_query": "Overheats at idle, heater blows lukewarm air"
        },
        {
            "id": "brake_system_analyzer",
            "name": "Brake System Safety & Rotor Runout Evaluator",
            "subsystem": "Hydraulic Brakes & ABS",
            "description": "Evaluates pad thickness in millimeters, pedal firmness/sponginess, rotor runout, and DOT fluid moisture boiling hazard.",
            "endpoint": "POST /api/analyzers/brake",
            "icon": "disc",
            "sample_query": "Pad thickness: 2mm, spongy pedal, pulls left"
        },
        {
            "id": "drivetrain_transmission_analyzer",
            "name": "Transmission & Drivetrain Health Analyzer",
            "subsystem": "Automatic, CVT & Manual Drivetrain",
            "description": "Analyzes gear slipping, shift harshness, torque converter shudder, and fluid oxidation/coolant contamination.",
            "endpoint": "POST /api/analyzers/drivetrain",
            "icon": "settings",
            "sample_query": "Torque converter shudder at 45 MPH or dark burnt ATF fluid"
        },
        {
            "id": "emissions_fuel_analyzer",
            "name": "Fuel Economy, Vacuum & Emissions Analyzer",
            "subsystem": "Fuel Delivery & Emissions",
            "description": "Interprets Short and Long Term Fuel Trims (STFT/LTFT), vacuum leaks, MAF degradation, and tailpipe smoke colors.",
            "endpoint": "POST /api/analyzers/emissions",
            "icon": "wind",
            "sample_query": "Idle LTFT: +22%, 2500 RPM LTFT: +4% (Vacuum leak)"
        },
        {
            "id": "interactive_guided_wizard",
            "name": "Multi-Step Interactive Diagnostic Wizard",
            "subsystem": "Universal Diagnostic Flow",
            "description": "Step-by-step decision tree that asks targeted symptoms to calculate composite failure probability and generate a work order.",
            "endpoint": "POST /api/analyzers/wizard/start and /step",
            "icon": "help-circle",
            "sample_query": "Engine cranks but won't start"
        }
    ]


__all__ = [
    "ProblemAnalysisResult",
    "DiagnosticCause",
    "ActionStep",
    "RiskLevel",
    "DifficultyLevel",
    "CostEstimate",
    "DTCProblemAnalyzer",
    "DTCAnalysisRequest",
    "FreezeFrameInput",
    "ElectricalProblemAnalyzer",
    "ElectricalAnalysisRequest",
    "ThermalProblemAnalyzer",
    "ThermalAnalysisRequest",
    "AcousticProblemAnalyzer",
    "AcousticAnalysisRequest",
    "BrakeProblemAnalyzer",
    "BrakeAnalysisRequest",
    "DrivetrainProblemAnalyzer",
    "DrivetrainAnalysisRequest",
    "EmissionsProblemAnalyzer",
    "EmissionsAnalysisRequest",
    "GuidedWizardEngine",
    "WizardStartRequest",
    "WizardStepRequest",
    "get_analyzer_catalog",
    "get_cost_estimate",
    "REPAIR_ESTIMATES"
]
