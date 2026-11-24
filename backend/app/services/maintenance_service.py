import json
import uuid
import logging
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any

from backend.app.config import settings
from backend.app.database import get_supabase_client
from backend.app.services.vehicle_service import get_vehicle_service
from backend.app.schemas.maintenance import (
    MaintenanceRecordCreate,
    MaintenanceRecordOut,
    MaintenanceOverview,
)

logger = logging.getLogger(__name__)

STANDARD_SERVICE_SCHEDULE = [
    {
        "service_type": "Engine Oil & Filter Change",
        "interval_months": 6,
        "interval_km": 10000,
        "notes": "Full synthetic motor oil and OEM spin-on filter renewal."
    },
    {
        "service_type": "Brake System & Pad Inspection",
        "interval_months": 12,
        "interval_km": 15000,
        "notes": "Inspect pad friction lining thickness (minimum 3mm) and caliper slide pins."
    },
    {
        "service_type": "Engine Coolant & Thermal Check",
        "interval_months": 24,
        "interval_km": 40000,
        "notes": "Check coolant specific gravity, freeze point, and radiator pressure cap."
    },
    {
        "service_type": "12V Battery Health & State-of-Charge",
        "interval_months": 6,
        "interval_km": 10000,
        "notes": "Test resting voltage (>=12.6V) and terminal post corrosion."
    },
    {
        "service_type": "Engine & Cabin Air Filters Renewal",
        "interval_months": 12,
        "interval_km": 20000,
        "notes": "Replace pleated intake air cleaner element and A/C pollen filter."
    },
    {
        "service_type": "Tire Rotation & Wheel Alignment",
        "interval_months": 6,
        "interval_km": 10000,
        "notes": "Rotate front-to-rear to equalize tread wear and verify steering alignment."
    }
]


class MaintenanceService:
    def __init__(self):
        self._supabase = None
        self._local_file = settings.data_processed_dir / "maintenance_store.json"
        self._local_records: Dict[str, Dict[str, Any]] = {}
        self._init_client()
        self._load_local_store()

    def _init_client(self):
        if settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key):
            try:
                self._supabase = get_supabase_client(admin=True)
            except Exception as e:
                logger.warning("MaintenanceService: Supabase admin client not active (%s). Trying anon.", e)
                try:
                    self._supabase = get_supabase_client(admin=False)
                except Exception as inner_e:
                    logger.warning("MaintenanceService: Supabase not active (%s). Using local store.", inner_e)

    def _load_local_store(self):
        if self._local_file.exists():
            try:
                with open(self._local_file, "r", encoding="utf-8") as f:
                    self._local_records = json.load(f)
            except Exception as e:
                logger.warning("Could not read local maintenance store: %s", e)
                self._local_records = {}

        if not self._local_records:
            # Seed standard maintenance schedule for default vehicle
            today = date.today()
            sample_odo = 45000
            for idx, item in enumerate(STANDARD_SERVICE_SCHEDULE):
                rec_id = f"maint-{idx + 1}"
                last_months_ago = (idx * 2) + 2
                last_service_dt = today - timedelta(days=last_months_ago * 30)
                last_odo = sample_odo - ((idx + 1) * 3500)
                next_dt = last_service_dt + timedelta(days=item["interval_months"] * 30)
                next_odo = last_odo + item["interval_km"]

                self._local_records[rec_id] = {
                    "id": rec_id,
                    "user_id": "default_user",
                    "vehicle_id": "veh-honda-civic-2022",
                    "service_type": item["service_type"],
                    "interval_months": item["interval_months"],
                    "interval_km": item["interval_km"],
                    "last_service_date": last_service_dt.isoformat(),
                    "last_service_odometer": last_odo,
                    "current_odometer": sample_odo,
                    "next_due_date": next_dt.isoformat(),
                    "next_due_odometer": next_odo,
                    "notes": item["notes"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            self._save_local_store()

    def _save_local_store(self):
        try:
            settings.data_processed_dir.mkdir(parents=True, exist_ok=True)
            with open(self._local_file, "w", encoding="utf-8") as f:
                json.dump(self._local_records, f, indent=2)
        except Exception as e:
            logger.error("Failed to save local maintenance store: %s", e)

    def _compute_status_and_remaining(
        self, rec: Dict[str, Any], current_odometer: int = 45000
    ) -> MaintenanceRecordOut:
        today = date.today()
        odo = rec.get("current_odometer") or current_odometer

        # Parse next due date
        next_due_date_str = rec.get("next_due_date")
        remaining_days = None
        if next_due_date_str:
            try:
                due_dt = date.fromisoformat(str(next_due_date_str)[:10])
                remaining_days = (due_dt - today).days
            except Exception:
                pass

        # Calculate remaining km
        next_odo = rec.get("next_due_odometer")
        remaining_km = None
        if next_odo is not None:
            try:
                remaining_km = int(next_odo) - int(odo)
            except Exception:
                pass

        # Evaluate status
        is_overdue = (remaining_days is not None and remaining_days < 0) or (remaining_km is not None and remaining_km <= 0)
        is_due_soon = (remaining_days is not None and 0 <= remaining_days <= 21) or (remaining_km is not None and 0 <= remaining_km <= 1500)

        if is_overdue:
            status = "overdue"
        elif is_due_soon:
            status = "due_soon"
        else:
            status = "upcoming"

        return MaintenanceRecordOut(
            id=str(rec["id"]),
            user_id=rec.get("user_id", "default_user"),
            vehicle_id=str(rec.get("vehicle_id")) if rec.get("vehicle_id") else None,
            service_type=rec["service_type"],
            interval_months=rec.get("interval_months", 6),
            interval_km=rec.get("interval_km", 10000),
            last_service_date=str(rec.get("last_service_date")) if rec.get("last_service_date") else None,
            last_service_odometer=rec.get("last_service_odometer"),
            current_odometer=odo,
            next_due_date=str(next_due_date_str) if next_due_date_str else None,
            next_due_odometer=next_odo,
            remaining_km=remaining_km,
            remaining_days=remaining_days,
            status=status,
            notes=rec.get("notes"),
            created_at=str(rec.get("created_at")) if rec.get("created_at") else None,
        )

    def get_overview(
        self,
        vehicle_id: Optional[str] = None,
        current_odometer: int = 45000,
        user_id: str = "default_user"
    ) -> MaintenanceOverview:
        records_raw: List[Dict[str, Any]] = []

        # 1. Query Supabase if active
        if self._supabase is not None:
            try:
                query = self._supabase.table("maintenance_records").select("*").eq("user_id", user_id)
                if vehicle_id:
                    query = query.eq("vehicle_id", vehicle_id)
                res = query.execute()
                if res.data:
                    records_raw = res.data
            except Exception as e:
                logger.warning("Supabase maintenance fetch failed: %s. Using local store.", e)

        # 2. Fallback to local records
        if not records_raw:
            local_user_recs = [r for r in self._local_records.values() if r.get("user_id") == user_id]
            if not local_user_recs and user_id == "default_user":
                local_user_recs = list(self._local_records.values())
            if vehicle_id:
                local_user_recs = [r for r in local_user_recs if str(r.get("vehicle_id")) == str(vehicle_id)]
            records_raw = local_user_recs

        processed: List[MaintenanceRecordOut] = [
            self._compute_status_and_remaining(r, current_odometer) for r in records_raw
        ]

        # Sort: overdue first, then due_soon, then upcoming
        order_map = {"overdue": 0, "due_soon": 1, "upcoming": 2, "completed": 3}
        processed.sort(
            key=lambda x: (
                order_map.get(x.status, 9),
                x.remaining_km if x.remaining_km is not None else 999999
            )
        )

        overdue_cnt = sum(1 for r in processed if r.status == "overdue")
        due_soon_cnt = sum(1 for r in processed if r.status == "due_soon")
        upcoming_cnt = sum(1 for r in processed if r.status == "upcoming")

        return MaintenanceOverview(
            total_records=len(processed),
            overdue_count=overdue_cnt,
            due_soon_count=due_soon_cnt,
            upcoming_count=upcoming_cnt,
            records=processed,
        )

    def add_record(
        self,
        record: MaintenanceRecordCreate,
        user_id: str = "default_user"
    ) -> MaintenanceRecordOut:
        new_id = str(uuid.uuid4())
        data = record.model_dump()
        data["id"] = new_id
        data["user_id"] = user_id
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Calculate next due date and odometer
        today = date.today()
        last_dt = (
            date.fromisoformat(str(data["last_service_date"])[:10])
            if data.get("last_service_date")
            else today
        )
        next_dt = last_dt + timedelta(days=data.get("interval_months", 6) * 30)
        data["next_due_date"] = next_dt.isoformat()

        last_odo = data.get("last_service_odometer") or data.get("current_odometer") or 45000
        data["next_due_odometer"] = last_odo + data.get("interval_km", 10000)

        # Ensure valid vehicle_id for Supabase foreign key constraint
        target_veh_id = data.get("vehicle_id")
        if self._supabase is not None:
            try:
                # If vehicle_id is missing or non-UUID, check/resolve to default vehicle
                is_valid_uuid = False
                if target_veh_id:
                    try:
                        uuid.UUID(str(target_veh_id))
                        is_valid_uuid = True
                    except ValueError:
                        is_valid_uuid = False

                if not is_valid_uuid:
                    veh_service = get_vehicle_service()
                    default_veh = veh_service.get_default_vehicle(user_id=user_id)
                    if default_veh:
                        target_veh_id = default_veh.id
                        data["vehicle_id"] = target_veh_id

                # Insert to Supabase
                res = self._supabase.table("maintenance_records").insert(data).execute()
                if res.data:
                    created_row = res.data[0]
                    self._local_records[new_id] = created_row
                    self._save_local_store()
                    return self._compute_status_and_remaining(created_row, created_row.get("current_odometer", 45000))
            except Exception as e:
                logger.warning("Supabase maintenance record insert failed: %s. Using local store.", e)

        self._local_records[new_id] = data
        self._save_local_store()
        return self._compute_status_and_remaining(data, data.get("current_odometer", 45000))

    def mark_completed(
        self,
        record_id: str,
        current_odometer: int,
        user_id: str = "default_user"
    ) -> Optional[MaintenanceRecordOut]:
        today = date.today()
        updated_data: Optional[Dict[str, Any]] = None

        if self._supabase is not None:
            try:
                res = self._supabase.table("maintenance_records").select("*").eq("id", record_id).execute()
                if res.data:
                    row = res.data[0]
                    # Ownership verification
                    if row.get("user_id") and row.get("user_id") != user_id and user_id != "default_user":
                        return None

                    next_dt = today + timedelta(days=row.get("interval_months", 6) * 30)
                    next_odo = current_odometer + row.get("interval_km", 10000)
                    update_payload = {
                        "last_service_date": today.isoformat(),
                        "last_service_odometer": current_odometer,
                        "current_odometer": current_odometer,
                        "next_due_date": next_dt.isoformat(),
                        "next_due_odometer": next_odo,
                        "status": "upcoming",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    upd_res = self._supabase.table("maintenance_records").update(update_payload).eq("id", record_id).execute()
                    if upd_res.data:
                        updated_data = upd_res.data[0]
            except Exception as e:
                logger.warning("Supabase mark_completed failed: %s. Using local store.", e)

        if not updated_data and record_id in self._local_records:
            rec = self._local_records[record_id]
            if rec.get("user_id") and rec.get("user_id") != user_id and user_id != "default_user":
                return None
            rec["last_service_date"] = today.isoformat()
            rec["last_service_odometer"] = current_odometer
            rec["current_odometer"] = current_odometer
            next_dt = today + timedelta(days=rec.get("interval_months", 6) * 30)
            rec["next_due_date"] = next_dt.isoformat()
            rec["next_due_odometer"] = current_odometer + rec.get("interval_km", 10000)
            rec["status"] = "upcoming"
            updated_data = rec

        if updated_data:
            self._local_records[record_id] = updated_data
            self._save_local_store()
            return self._compute_status_and_remaining(updated_data, current_odometer)

        return None


_maintenance_service_instance = None


def get_maintenance_service() -> MaintenanceService:
    global _maintenance_service_instance
    if _maintenance_service_instance is None:
        _maintenance_service_instance = MaintenanceService()
    return _maintenance_service_instance
