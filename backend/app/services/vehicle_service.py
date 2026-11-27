import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.app.config import settings
from backend.app.database import get_supabase_client
from backend.app.schemas.vehicles import VehicleCreate, VehicleUpdate, VehicleOut

logger = logging.getLogger(__name__)

# Valid database columns in public.vehicles on Supabase
SUPABASE_VEHICLE_COLUMNS = {
    "id", "user_id", "make", "model", "year", "fuel_type",
    "engine_variant", "nickname", "odometer", "is_default",
    "metadata", "created_at", "updated_at"
}

DEFAULT_VEHICLE_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "default-honda-civic-2022"))


def _is_valid_uuid(val: Any) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False


def _ensure_uuid(val: Any) -> str:
    if _is_valid_uuid(val):
        return str(val)
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(val)))


def _sanitize_for_supabase(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes payload so only valid columns in Supabase vehicles table are sent."""
    clean: Dict[str, Any] = {}
    metadata = dict(payload.get("metadata") or {})

    # Preserve city inside metadata for Supabase compatibility
    if "city" in payload and payload["city"]:
        metadata["city"] = payload["city"]

    for k, v in payload.items():
        if k in SUPABASE_VEHICLE_COLUMNS:
            clean[k] = v

    # Fallback: if odometer is missing but mileage_km was passed
    if "odometer" not in clean and "mileage_km" in payload and payload["mileage_km"] is not None:
        clean["odometer"] = payload["mileage_km"]

    clean["metadata"] = metadata
    return clean


def _row_to_vehicle_out(row: Dict[str, Any]) -> VehicleOut:
    """Converts a database row or cache dict to VehicleOut with city and mileage_km synced."""
    data = dict(row)
    data["id"] = _ensure_uuid(data.get("id", str(uuid.uuid4())))
    metadata = dict(data.get("metadata") or {})
    if not data.get("city"):
        data["city"] = metadata.get("city", "Bengaluru")
    if data.get("mileage_km") is None:
        data["mileage_km"] = data.get("odometer", 45000)
    return VehicleOut(**data)


class VehicleService:
    def __init__(self):
        self._supabase = None
        self._local_file = settings.data_processed_dir / "vehicles_store.json"
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._init_client()
        self._load_local_store()
        self._sync_with_supabase()

    def _init_client(self):
        if settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key):
            try:
                # Use admin client for backend service operations to ensure persistent data flow
                self._supabase = get_supabase_client(admin=True)
            except Exception as e:
                logger.warning("VehicleService: Supabase admin client failed (%s). Trying default client.", e)
                try:
                    self._supabase = get_supabase_client(admin=False)
                except Exception as inner_e:
                    logger.warning("VehicleService: Supabase not active (%s). Using local storage.", inner_e)

    def _load_local_store(self):
        if self._local_file.exists():
            try:
                with open(self._local_file, "r", encoding="utf-8") as f:
                    raw_cache = json.load(f)
                    migrated: Dict[str, Dict[str, Any]] = {}
                    for k, v in raw_cache.items():
                        new_id = _ensure_uuid(v.get("id", k))
                        v["id"] = new_id
                        migrated[new_id] = v
                    self._local_cache = migrated
            except Exception as e:
                logger.warning("Could not read local vehicles store: %s", e)
                self._local_cache = {}

        if not self._local_cache:
            # Seed with default vehicle (Honda Civic 2022) with RFC-compliant UUID
            self._local_cache[DEFAULT_VEHICLE_UUID] = {
                "id": DEFAULT_VEHICLE_UUID,
                "user_id": "default_user",
                "make": "Honda",
                "model": "Civic",
                "year": 2022,
                "fuel_type": "Petrol",
                "engine_variant": "1.5L VTEC Turbo",
                "nickname": "Daily Sedan",
                "odometer": 45000,
                "mileage_km": 45000,
                "city": "Bengaluru",
                "is_default": True,
                "metadata": {"city": "Bengaluru"},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save_local_store()

    def _sync_with_supabase(self):
        """Ensures Supabase vehicles table has at least one active vehicle and local cache is up-to-date."""
        if self._supabase is None:
            return
        try:
            res = self._supabase.table("vehicles").select("*").eq("user_id", "default_user").execute()
            if res.data:
                for row in res.data:
                    rid = _ensure_uuid(row["id"])
                    row["id"] = rid
                    self._local_cache[rid] = row
                self._save_local_store()
            elif not res.data and self._local_cache:
                # Seed initial default vehicle directly into Supabase
                default_veh = next((v for v in self._local_cache.values() if v.get("is_default")), None)
                if not default_veh:
                    default_veh = list(self._local_cache.values())[0]
                clean = _sanitize_for_supabase(default_veh)
                self._supabase.table("vehicles").insert(clean).execute()
                logger.info("VehicleService: Seeded default vehicle into Supabase.")
        except Exception as e:
            logger.warning("VehicleService: Supabase synchronization check skipped: %s", e)

    def _save_local_store(self):
        try:
            settings.data_processed_dir.mkdir(parents=True, exist_ok=True)
            with open(self._local_file, "w", encoding="utf-8") as f:
                json.dump(self._local_cache, f, indent=2)
        except Exception as e:
            logger.error("Failed to persist local vehicles store: %s", e)

    def list_vehicles(self, user_id: str = "default_user") -> List[VehicleOut]:
        if self._supabase is not None:
            try:
                res = self._supabase.table("vehicles").select("*").eq("user_id", user_id).execute()
                if res.data:
                    for row in res.data:
                        rid = _ensure_uuid(row["id"])
                        row["id"] = rid
                        self._local_cache[rid] = row
                    return [_row_to_vehicle_out(row) for row in res.data]
            except Exception as e:
                logger.warning("Supabase vehicles fetch failed: %s. Falling back to local store.", e)

        # Fallback to local store scoped to user_id
        user_vehs = [v for v in self._local_cache.values() if v.get("user_id") == user_id]
        if not user_vehs and user_id == "default_user" and self._local_cache:
            user_vehs = list(self._local_cache.values())
        return [_row_to_vehicle_out(v) for v in user_vehs]

    def get_vehicle(self, vehicle_id: str, user_id: Optional[str] = None) -> Optional[VehicleOut]:
        canonical_id = _ensure_uuid(vehicle_id)
        if self._supabase is not None and _is_valid_uuid(canonical_id):
            try:
                query = self._supabase.table("vehicles").select("*").eq("id", canonical_id)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res.data:
                    return _row_to_vehicle_out(res.data[0])
            except Exception as e:
                logger.warning("Supabase vehicle get failed: %s", e)

        v = self._local_cache.get(canonical_id) or self._local_cache.get(vehicle_id)
        if v:
            if user_id and v.get("user_id") != user_id:
                return None  # Ownership check failed
            return _row_to_vehicle_out(v)
        return None

    def get_default_vehicle(self, user_id: str = "default_user") -> Optional[VehicleOut]:
        all_vehs = self.list_vehicles(user_id)
        for v in all_vehs:
            if v.is_default:
                return v
        return all_vehs[0] if all_vehs else None

    def create_vehicle(self, vehicle: VehicleCreate, user_id: str = "default_user") -> VehicleOut:
        now = datetime.now(timezone.utc).isoformat()
        new_id = str(uuid.uuid4())
        data = vehicle.model_dump()
        data["id"] = new_id
        data["user_id"] = user_id
        data["created_at"] = now
        data["updated_at"] = now

        # If set as default, reset other defaults for this user
        if data.get("is_default"):
            for v in self._local_cache.values():
                if v.get("user_id") == user_id:
                    v["is_default"] = False

        if self._supabase is not None:
            try:
                if data.get("is_default"):
                    self._supabase.table("vehicles").update({"is_default": False}).eq("user_id", user_id).execute()
                clean_payload = _sanitize_for_supabase(data)
                res = self._supabase.table("vehicles").insert(clean_payload).execute()
                if res.data:
                    created = res.data[0]
                    # Preserve full model fields in local cache
                    data.update(created)
                    self._local_cache[new_id] = data
                    self._save_local_store()
                    return _row_to_vehicle_out(data)
            except Exception as e:
                logger.warning("Supabase vehicle insert failed: %s. Using local store.", e)

        self._local_cache[new_id] = data
        self._save_local_store()
        return _row_to_vehicle_out(data)

    def update_vehicle(
        self,
        vehicle_id: str,
        updates: VehicleUpdate,
        user_id: str = "default_user"
    ) -> Optional[VehicleOut]:
        canonical_id = _ensure_uuid(vehicle_id)
        existing = self.get_vehicle(canonical_id, user_id=user_id) or self.get_vehicle(vehicle_id, user_id=user_id)
        if not existing:
            return None

        update_dict = updates.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        if update_dict.get("is_default"):
            for v in self._local_cache.values():
                if v.get("user_id") == user_id:
                    v["is_default"] = False

        if self._supabase is not None and _is_valid_uuid(canonical_id):
            try:
                if update_dict.get("is_default"):
                    self._supabase.table("vehicles").update({"is_default": False}).eq("user_id", user_id).execute()
                clean_updates = _sanitize_for_supabase(update_dict)
                res = self._supabase.table("vehicles").update(clean_updates).eq("id", canonical_id).eq("user_id", user_id).execute()
                if res.data:
                    updated = res.data[0]
                    cached = self._local_cache.get(canonical_id, existing.model_dump())
                    cached.update(updated)
                    if "city" in update_dict and update_dict["city"]:
                        cached["city"] = update_dict["city"]
                    if "mileage_km" in update_dict and update_dict["mileage_km"] is not None:
                        cached["mileage_km"] = update_dict["mileage_km"]
                        cached["odometer"] = update_dict["mileage_km"]
                    self._local_cache[canonical_id] = cached
                    self._save_local_store()
                    return _row_to_vehicle_out(cached)
            except Exception as e:
                logger.warning("Supabase vehicle update failed: %s", e)

        data = self._local_cache.get(canonical_id, existing.model_dump())
        data.update(update_dict)
        if "mileage_km" in update_dict and update_dict["mileage_km"] is not None:
            data["odometer"] = update_dict["mileage_km"]
        self._local_cache[canonical_id] = data
        self._save_local_store()
        return _row_to_vehicle_out(data)

    def delete_vehicle(self, vehicle_id: str, user_id: str = "default_user") -> bool:
        canonical_id = _ensure_uuid(vehicle_id)
        existing = self.get_vehicle(canonical_id, user_id=user_id) or self.get_vehicle(vehicle_id, user_id=user_id)
        if not existing:
            return False

        if self._supabase is not None and _is_valid_uuid(canonical_id):
            try:
                self._supabase.table("vehicles").delete().eq("id", canonical_id).eq("user_id", user_id).execute()
            except Exception as e:
                logger.warning("Supabase vehicle delete failed: %s", e)

        removed = False
        for target_id in (canonical_id, vehicle_id):
            if target_id in self._local_cache:
                del self._local_cache[target_id]
                removed = True

        if removed:
            self._save_local_store()
            return True
        return False


_vehicle_service_instance = None


def get_vehicle_service() -> VehicleService:
    global _vehicle_service_instance
    if _vehicle_service_instance is None:
        _vehicle_service_instance = VehicleService()
    return _vehicle_service_instance

