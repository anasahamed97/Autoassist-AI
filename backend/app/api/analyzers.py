"""
AutoAssist AI - Automotive Problem Analyzers API Router
Exposes dedicated endpoints for DTC codes, electrical multimeter, thermal cooling,
NVH acoustics, braking safety, transmission, emissions, and interactive guided wizard.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status

from backend.app.analyzers import (
    get_analyzer_catalog,
    ProblemAnalysisResult,
    DTCProblemAnalyzer, DTCAnalysisRequest,
    ElectricalProblemAnalyzer, ElectricalAnalysisRequest,
    ThermalProblemAnalyzer, ThermalAnalysisRequest,
    AcousticProblemAnalyzer, AcousticAnalysisRequest,
    BrakeProblemAnalyzer, BrakeAnalysisRequest,
    DrivetrainProblemAnalyzer, DrivetrainAnalysisRequest,
    EmissionsProblemAnalyzer, EmissionsAnalysisRequest,
    GuidedWizardEngine, WizardStartRequest, WizardStepRequest,
    REPAIR_ESTIMATES
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyzers", tags=["Problem Analyzers"])

# Singletons for memory efficiency
_dtc_analyzer = DTCProblemAnalyzer()
_electrical_analyzer = ElectricalProblemAnalyzer()
_thermal_analyzer = ThermalProblemAnalyzer()
_acoustic_analyzer = AcousticProblemAnalyzer()
_brake_analyzer = BrakeProblemAnalyzer()
_drivetrain_analyzer = DrivetrainProblemAnalyzer()
_emissions_analyzer = EmissionsProblemAnalyzer()
_wizard_engine = GuidedWizardEngine()


@router.get(
    "/catalog",
    response_model=List[Dict[str, Any]],
    summary="List all available problem analyzers",
    description="Returns metadata, subsystems, icons, and sample queries for all installed problem analyzers."
)
async def list_analyzers():
    return get_analyzer_catalog()


@router.get(
    "/repairs/price-guide",
    summary="Standard automotive repair pricing and difficulty guide",
    description="Returns repair pricing benchmarks, labor hours, and difficulty ratings."
)
async def get_price_guide():
    return REPAIR_ESTIMATES


@router.post(
    "/dtc",
    response_model=ProblemAnalysisResult,
    summary="Analyze OBD-II Diagnostic Trouble Code",
    description="Analyzes P, C, B, and U trouble codes with freeze-frame sensor values and step-by-step repair guides."
)
async def analyze_dtc(request: DTCAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _dtc_analyzer.analyze(request)
    except Exception as e:
        logger.error("DTC Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DTC analysis failed: {str(e)}"
        )


@router.post(
    "/electrical",
    response_model=ProblemAnalysisResult,
    summary="Starting & Charging Multimeter Analyzer",
    description="Analyzes battery resting voltage, starter cranking drop, alternator regulation, and parasitic drain."
)
async def analyze_electrical(request: ElectricalAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _electrical_analyzer.analyze(request)
    except Exception as e:
        logger.error("Electrical Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Electrical analysis failed: {str(e)}"
        )


@router.post(
    "/thermal",
    response_model=ProblemAnalysisResult,
    summary="Engine Cooling & Overheating Problem Analyzer",
    description="Diagnoses overheating conditions (idle vs highway, fan, thermostat, water pump, and head gasket)."
)
async def analyze_thermal(request: ThermalAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _thermal_analyzer.analyze(request)
    except Exception as e:
        logger.error("Thermal Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Thermal analysis failed: {str(e)}"
        )


@router.post(
    "/acoustic",
    response_model=ProblemAnalysisResult,
    summary="NVH Sound & Mechanical Vibration Analyzer",
    description="Isolates failing mechanical components based on sound type, vehicle location, and driving conditions."
)
async def analyze_acoustic(request: AcousticAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _acoustic_analyzer.analyze(request)
    except Exception as e:
        logger.error("Acoustic Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Acoustic analysis failed: {str(e)}"
        )


@router.post(
    "/brake",
    response_model=ProblemAnalysisResult,
    summary="Brake System Safety & Wear Evaluator",
    description="Evaluates pad thickness in mm, pedal travel/firmness, rotor runout, and fluid boiling safety."
)
async def analyze_brake(request: BrakeAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _brake_analyzer.analyze(request)
    except Exception as e:
        logger.error("Brake Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brake analysis failed: {str(e)}"
        )


@router.post(
    "/drivetrain",
    response_model=ProblemAnalysisResult,
    summary="Transmission & Drivetrain Health Analyzer",
    description="Diagnoses automatic, CVT, and manual transmissions, fluid degradation, torque converter shudder, and slipping."
)
async def analyze_drivetrain(request: DrivetrainAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _drivetrain_analyzer.analyze(request)
    except Exception as e:
        logger.error("Drivetrain Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drivetrain analysis failed: {str(e)}"
        )


@router.post(
    "/emissions",
    response_model=ProblemAnalysisResult,
    summary="Fuel Trim, Vacuum & Emissions Analyzer",
    description="Calculates STFT/LTFT stoichiometric imbalances, vacuum leaks, MAF contamination, and exhaust colors."
)
async def analyze_emissions(request: EmissionsAnalysisRequest) -> ProblemAnalysisResult:
    try:
        return _emissions_analyzer.analyze(request)
    except Exception as e:
        logger.error("Emissions Analysis error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emissions analysis failed: {str(e)}"
        )


@router.post(
    "/wizard/start",
    summary="Start Guided Diagnostic Wizard",
    description="Returns targeted diagnostic questions for a selected automotive symptom domain."
)
async def start_wizard(request: WizardStartRequest):
    questions = _wizard_engine.get_domain_questions(request.domain)
    return {
        "domain": request.domain,
        "questions": [q.model_dump() for q in questions]
    }


@router.post(
    "/wizard/step",
    response_model=ProblemAnalysisResult,
    summary="Evaluate Guided Wizard Answers",
    description="Processes user answers from the interactive wizard to generate a comprehensive diagnostic report."
)
async def evaluate_wizard_step(request: WizardStepRequest) -> ProblemAnalysisResult:
    try:
        return _wizard_engine.evaluate_step(request)
    except Exception as e:
        logger.error("Wizard Step error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wizard evaluation failed: {str(e)}"
        )
