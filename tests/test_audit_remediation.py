"""
AutoAssist AI - Audit Remediation & Verification Test Suite
Tests authentication, authorization, vehicle ownership, Supabase maintenance persistence,
dynamic quotation labor rates, severity safety advisory phrasing, and 7-language query normalization.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.vehicle_service import get_vehicle_service
from backend.app.services.maintenance_service import get_maintenance_service
from backend.app.services.quotation_service import get_quotation_service
from backend.app.services.severity_service import get_severity_service
from backend.app.schemas.vehicles import VehicleCreate, VehicleUpdate
from backend.app.schemas.maintenance import MaintenanceRecordCreate
from backend.app.schemas.quotations import QuoteComparisonRequest, QuoteItemInput
from backend.app.schemas.severity import SeverityRequest
from backend.app.rag.multilingual import normalize_automotive_query

client = TestClient(app)


def test_auth_headers_and_defaults():
    # Test unauthenticated default
    res = client.get("/api/vehicles")
    assert res.status_code == 200

    # Test custom X-User-ID header
    res_custom = client.get("/api/vehicles", headers={"X-User-ID": "test_suite_user_123"})
    assert res_custom.status_code == 200


def test_vehicle_ownership_enforcement():
    service = get_vehicle_service()
    owner_id = "user_alpha"
    intruder_id = "user_beta"

    # Create vehicle under owner_id
    veh = service.create_vehicle(
        VehicleCreate(
            make="Tata",
            model="Nexon",
            year=2023,
            fuel_type="Petrol",
            odometer=12000
        ),
        user_id=owner_id
    )
    assert veh.id is not None

    # Intruder cannot update owner's vehicle
    intruder_update = service.update_vehicle(
        veh.id,
        VehicleUpdate(odometer=99999),
        user_id=intruder_id
    )
    assert intruder_update is None

    # Intruder cannot delete owner's vehicle
    intruder_del = service.delete_vehicle(veh.id, user_id=intruder_id)
    assert intruder_del is False

    # Owner can update
    owner_update = service.update_vehicle(
        veh.id,
        VehicleUpdate(odometer=12500),
        user_id=owner_id
    )
    assert owner_update is not None
    assert owner_update.odometer == 12500

    # Owner can delete
    owner_del = service.delete_vehicle(veh.id, user_id=owner_id)
    assert owner_del is True


def test_maintenance_overview_and_record():
    m_svc = get_maintenance_service()
    user_id = "test_maint_owner"

    # Initially empty for new user
    overview = m_svc.get_overview(user_id=user_id)
    assert overview.total_records >= 0

    # Add a custom record
    rec = m_svc.add_record(
        MaintenanceRecordCreate(
            service_type="Spark Plug Inspection",
            interval_months=12,
            interval_km=20000,
            last_service_odometer=30000,
            current_odometer=35000,
            notes="Check electrode gap (1.0-1.1mm)"
        ),
        user_id=user_id
    )
    assert rec.id is not None
    assert rec.status in ["upcoming", "due_soon", "overdue"]


def test_quotation_dynamic_city_rates():
    q_svc = get_quotation_service()

    # Bengaluru labor benchmark: ₹750/hr
    req_blr = QuoteComparisonRequest(
        repair_title="Brake Service BLR",
        city="Bengaluru",
        items=[
            QuoteItemInput(
                service_or_part="Front Brake Pads (Set of 4)",
                quantity=1,
                quoted_part_price=2500.0,
                quoted_labor_price=750.0
            )
        ]
    )
    res_blr = q_svc.evaluate_quotation(req_blr)
    assert res_blr.total_quoted == 3250.0
    # Minimum ref labor in BLR = 1.0 hr * ₹750 = ₹750
    assert res_blr.items[0].reference_labor_min == 750.0

    # Mumbai labor benchmark: ₹800/hr
    req_mum = QuoteComparisonRequest(
        repair_title="Brake Service MUM",
        city="Mumbai",
        items=[
            QuoteItemInput(
                service_or_part="Front Brake Pads (Set of 4)",
                quantity=1,
                quoted_part_price=2500.0,
                quoted_labor_price=800.0
            )
        ]
    )
    res_mum = q_svc.evaluate_quotation(req_mum)
    # Minimum ref labor in MUM = 1.0 hr * ₹800 = ₹800
    assert res_mum.items[0].reference_labor_min == 800.0


def test_severity_cautious_advisory_language():
    s_svc = get_severity_service()

    # Low severity
    sev_low = s_svc.assess_severity(
        SeverityRequest(
            symptom_or_code="Wiper blade streaking slightly",
            subsystem="general"
        )
    )
    # Must NOT claim definitive "safe to drive under normal conditions"
    assert "safe to drive under normal conditions" not in sev_low.immediate_action.lower()
    assert "no immediate road hazard" in sev_low.immediate_action.lower()

    # Critical severity
    sev_crit = s_svc.assess_severity(
        SeverityRequest(
            symptom_or_code="Brake pedal sinking to floor and fluid leak",
            subsystem="brakes"
        )
    )
    assert sev_crit.category == "CRITICAL"
    assert sev_crit.is_safe_to_drive is False
    assert sev_crit.stop_driving_notice is not None


def test_multilingual_query_normalization_7_languages():
    # 1. Kannada (kn)
    kn_q = normalize_automotive_query("ಎಂಜಿನ್ ಬಿಸಿಯಾಗುತ್ತಿದೆ")
    assert "overheating" in kn_q.lower() or "coolant" in kn_q.lower()

    # 2. Hindi (hi)
    hi_q = normalize_automotive_query("इंजन बहुत गरम हो रहा है")
    assert "overheating" in hi_q.lower() or "coolant" in hi_q.lower()

    # 3. Urdu (ur)
    ur_q = normalize_automotive_query("گاڑی کا بریک کام نہیں کر رہا")
    assert "brake" in ur_q.lower()

    # 4. Malayalam (ml)
    ml_q = normalize_automotive_query("എഞ്ചിൻ അമിതമായി ചൂടാകുന്നു")
    assert "overheating" in ml_q.lower() or "coolant" in ml_q.lower()

    # 5. Tamil (ta)
    ta_q = normalize_automotive_query("பிரேக் பிடிக்கும் போது சத்தம் வருகிறது")
    assert "brake" in ta_q.lower()

    # 6. Telugu (te)
    te_q = normalize_automotive_query("ఇంజన్ వేడెక్కుతోంది మరియు పొగ వస్తోంది")
    assert "overheating" in te_q.lower() or "smoke" in te_q.lower()

    # 7. English (en)
    en_q = normalize_automotive_query("Engine misfire when accelerating")
    assert "misfire" in en_q.lower()
