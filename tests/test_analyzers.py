"""
AutoAssist AI - Comprehensive Problem Analyzers & Website Test Suite
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_analyzer_catalog():
    response = client.get("/api/analyzers/catalog")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8
    analyzer_ids = [a["id"] for a in data]
    assert "dtc_code_analyzer" in analyzer_ids
    assert "electrical_multimeter_analyzer" in analyzer_ids
    assert "thermal_cooling_analyzer" in analyzer_ids
    assert "brake_system_analyzer" in analyzer_ids


def test_price_guide_endpoint():
    response = client.get("/api/analyzers/repairs/price-guide")
    assert response.status_code == 200
    data = response.json()
    assert "battery_replacement" in data
    assert "thermostat_replacement" in data
    assert "parts" in data["battery_replacement"]
    assert "₹" in data["battery_replacement"]["parts"]


def test_dtc_analyzer_p0300():
    payload = {
        "code": "P0300",
        "freeze_frame": {
            "engine_rpm": 750,
            "short_term_fuel_trim_pct": 2.5,
            "long_term_fuel_trim_pct": 18.0,
            "engine_coolant_temp_f": 195,
            "battery_voltage": 14.1
        },
        "include_rag_chunks": True
    }
    response = client.post("/api/analyzers/dtc", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analyzer_id"] == "dtc_code_analyzer"
    assert "P0300" in data["primary_verdict"]
    assert len(data["probable_causes"]) > 0
    assert len(data["action_plan"]) > 0
    assert data["cost_estimate"] is not None
    assert "₹" in data["cost_estimate"]["diy_parts_cost_range_inr"]


def test_electrical_analyzer_dead_battery():
    payload = {
        "resting_voltage": 11.6,
        "cranking_voltage": 8.5,
        "alternator_running_voltage": 14.1,
        "parasitic_draw_ma": 30.0,
        "include_rag_chunks": False
    }
    response = client.post("/api/analyzers/electrical", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "CRITICAL"
    assert data["is_safe_to_drive"] is False
    assert data["telemetry_summary"]["calculated_state_of_charge_pct"] == 0


def test_thermal_analyzer_idle_overheating():
    payload = {
        "driving_condition": "idle_traffic",
        "coolant_level": "normal",
        "electric_fan_running": "no_not_spinning",
        "cabin_heater_output": "hot",
        "hose_temperature_differential": "both_hot",
        "white_exhaust_smoke_or_milky_oil": False,
        "include_rag_chunks": False
    }
    response = client.post("/api/analyzers/thermal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Fan" in data["primary_verdict"] or "Fan" in data["probable_causes"][0]["title"]
    assert data["urgency"] == "CRITICAL"


def test_acoustic_analyzer_brake_grind():
    payload = {
        "sound_type": "grind_metal",
        "location": "front_wheel_brakes",
        "condition": "when_braking",
        "speed_dependent": True,
        "rpm_dependent": False,
        "include_rag_chunks": False
    }
    response = client.post("/api/analyzers/acoustic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Brake" in data["primary_verdict"] or "Brake" in data["probable_causes"][0]["title"]
    assert data["urgency"] == "HIGH"


def test_brake_analyzer_critical_wear():
    payload = {
        "pad_thickness_mm": 1.5,
        "pedal_feel": "sinks_to_floor",
        "rotor_condition": "grooved_scored",
        "pulls_when_braking": "pulls_left",
        "abs_warning_light": True,
        "include_rag_chunks": False
    }
    response = client.post("/api/analyzers/brake", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "CRITICAL"
    assert data["is_safe_to_drive"] is False


def test_drivetrain_analyzer_coolant_breach():
    payload = {
        "transmission_type": "automatic_torque_converter",
        "symptom": "slipping_rpm_flares",
        "fluid_color": "milky_strawberry_shake",
        "fluid_level": "normal",
        "include_rag_chunks": False
    }
    response = client.post("/api/analyzers/drivetrain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "CRITICAL"
    assert "Coolant" in data["primary_verdict"] or "Coolant" in data["probable_causes"][0]["title"]


def test_emissions_analyzer_vacuum_leak():
    payload = {
        "stft_idle_pct": 4.0,
        "ltft_idle_pct": 21.0,
        "stft_2500rpm_pct": 1.0,
        "ltft_2500rpm_pct": 3.0,
        "exhaust_smoke_color": "none",
        "raw_fuel_odor": False,
        "include_rag_chunks": False
    }
    response = client.post("/api/analyzers/emissions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Vacuum Leak" in data["primary_verdict"] or "Vacuum" in data["probable_causes"][0]["title"]


def test_wizard_start_and_evaluate():
    start_resp = client.post("/api/analyzers/wizard/start", json={"domain": "no_start"})
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert len(start_data["questions"]) > 0

    step_resp = client.post("/api/analyzers/wizard/step", json={
        "domain": "no_start",
        "answers": {
            "crank_behavior": "rapid_clicking",
            "headlights_test": "very_dim"
        },
        "include_rag_chunks": False
    })
    assert step_resp.status_code == 200
    step_data = step_resp.json()
    assert "Battery" in step_data["primary_verdict"]


def test_web_app_html_serving():
    # Direct /app endpoint
    resp = client.get("/app")
    assert resp.status_code == 200
    assert "AutoAssist AI" in resp.text
    assert "<!DOCTYPE html>" in resp.text

    # Root endpoint with browser accept header
    browser_resp = client.get("/", headers={"accept": "text/html,application/xhtml+xml"})
    assert browser_resp.status_code == 200
    assert "<!DOCTYPE html>" in browser_resp.text
    # Verify API Docs option was removed from home page
    assert "📚 API Docs" not in browser_resp.text
