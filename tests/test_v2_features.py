import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_vehicles_api():
    # 1. List vehicles
    res = client.get("/api/vehicles")
    assert res.status_code == 200
    vehs = res.json()
    assert isinstance(vehs, list)
    assert len(vehs) >= 1

    # 2. Get default vehicle
    res_def = client.get("/api/vehicles/default")
    assert res_def.status_code == 200
    default_veh = res_def.json()
    assert "make" in default_veh
    assert "model" in default_veh

    # 3. Create vehicle
    new_veh = {
        "make": "Toyota",
        "model": "Corolla",
        "year": 2023,
        "fuel_type": "Hybrid",
        "engine_variant": "1.8L Hybrid",
        "nickname": "Work Car",
        "odometer": 28000,
        "is_default": False
    }
    res_create = client.post("/api/vehicles", json=new_veh)
    assert res_create.status_code == 201
    created = res_create.json()
    assert created["make"] == "Toyota"
    created_id = created["id"]

    # 4. Update vehicle
    res_update = client.put(f"/api/vehicles/{created_id}", json={"odometer": 29500})
    assert res_update.status_code == 200
    assert res_update.json()["odometer"] == 29500

    # 5. Delete vehicle
    res_del = client.delete(f"/api/vehicles/{created_id}")
    assert res_del.status_code == 204


def test_pricing_and_estimator():
    # 1. Catalog list
    res_cat = client.get("/api/pricing/catalog")
    assert res_cat.status_code == 200
    items = res_cat.json()
    assert len(items) >= 10

    # 2. Estimate matched item (Brake pads)
    res_est = client.post("/api/pricing/estimate", json={
        "issue_or_part": "front brake pads",
        "make": "Honda",
        "model": "Civic",
        "city": "Bengaluru"
    })
    assert res_est.status_code == 200
    data = res_est.json()
    assert data["matched"] is True
    assert "Brake Pads" in data["part_name"]
    assert data["total_min"] > 0
    assert "₹" in data["total_estimated_cost_inr"]

    # 3. Missing item handling (No fictitious pricing)
    res_missing = client.post("/api/pricing/estimate", json={
        "issue_or_part": "flux capacitor 9000",
        "make": "DeLorean",
        "model": "DMC-12"
    })
    assert res_missing.status_code == 200
    missing_data = res_missing.json()
    assert missing_data["matched"] is False
    assert "unavailable" in missing_data["part_name"].lower()


def test_mechanic_quotation_checker():
    # Quote with a mix of items
    payload = {
        "repair_title": "100,000 km Major Service & Brake Repair",
        "garage_name": "Apex Auto Garage",
        "make": "Honda",
        "model": "Civic",
        "city": "Bengaluru",
        "items": [
            {
                "service_or_part": "Front Brake Pads",
                "quantity": 1,
                "quoted_part_price": 5500.0,  # Above reference
                "quoted_labor_price": 1200.0,
                "quoted_additional": 200.0
            },
            {
                "service_or_part": "Engine Oil Filter",
                "quantity": 1,
                "quoted_part_price": 450.0,   # Within reference
                "quoted_labor_price": 200.0,
                "quoted_additional": 50.0
            }
        ]
    }
    res = client.post("/api/quotations/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "total_quoted" in data
    assert len(data["items"]) == 2
    assert len(data["suggested_mechanic_questions"]) >= 3
    assert "educational_note" in data


def test_maintenance_service_and_reminders():
    # 1. Overview
    res = client.get("/api/maintenance/overview?current_odometer=45000")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] >= 1
    assert "records" in data

    # 2. Add maintenance record
    new_rec = {
        "service_type": "Spark Plugs Replacement",
        "interval_months": 24,
        "interval_km": 40000,
        "last_service_date": "2024-01-15",
        "last_service_odometer": 35000,
        "current_odometer": 45000,
        "notes": "Laser iridium spark plugs renewal."
    }
    res_add = client.post("/api/maintenance/records", json=new_rec)
    assert res_add.status_code == 201
    created = res_add.json()
    rec_id = created["id"]
    assert created["status"] in ["upcoming", "due_soon", "overdue"]

    # 3. Mark completed
    res_comp = client.post(f"/api/maintenance/records/{rec_id}/complete?current_odometer=46000")
    assert res_comp.status_code == 200
    assert res_comp.json()["last_service_odometer"] == 46000


def test_severity_assessment():
    # 1. Critical safety trigger (Brake failure)
    res_crit = client.post("/api/severity/assess", json={
        "symptom_or_code": "Brake pedal sinking to floor and fluid leak puddle",
        "can_vehicle_steer_and_stop": False
    })
    assert res_crit.status_code == 200
    data_crit = res_crit.json()
    assert data_crit["category"] == "CRITICAL"
    assert data_crit["is_safe_to_drive"] is False
    assert data_crit["stop_driving_notice"] is not None

    # 2. Moderate inspection trigger (Check engine misfire)
    res_mod = client.post("/api/severity/assess", json={
        "symptom_or_code": "Check Engine Light on with P0300 cylinder misfire",
        "can_vehicle_steer_and_stop": True
    })
    assert res_mod.status_code == 200
    data_mod = res_mod.json()
    assert data_mod["category"] == "MODERATE"
    assert data_mod["is_safe_to_drive"] is True

    # 3. Low maintenance trigger
    res_low = client.post("/api/severity/assess", json={
        "symptom_or_code": "Windshield washer fluid low and wiper blade streak",
        "can_vehicle_steer_and_stop": True
    })
    assert res_low.status_code == 200
    assert res_low.json()["category"] == "LOW"


def test_dual_view_manual_explanation():
    res = client.post("/api/rag/explain", json={
        "query": "What causes engine overheating at idle?",
        "top_k": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert "technical_passages" in data
    assert "simple_explanation" in data
    se = data["simple_explanation"]
    assert "what_does_it_mean" in se
    assert "why_does_it_happen" in se
    assert len(se["what_should_you_do"]) >= 1
    assert len(se["suggested_mechanic_questions"]) >= 1
