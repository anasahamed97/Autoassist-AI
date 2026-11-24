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


class VehicleService:
    def __init__(self):
        self._supabase = None
        self._local_file = settings.data_processed_dir / "vehicles_store.json"
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._init_client()
        self._load_local_store()

    def _init_client(self):
        if settings.supabase_url and (settings.supabase_key or settings.supabase_service_role_key):
            try:
                self._supabase = get_supabase_client(admin=False)
            except Exception as e:
                logger.warning("VehicleService: Supabase not active (%s). Using local storage.", e)

    def _load_local_store(self):
        if self._local_file.exists():
            try:
                with open(self._local_file, "r", encoding="utf-8") as f:
                    self._local_cache = json.load(f)
            except Exception as e:
                logger.warning("Could not read local vehicles store: %s", e)
                self._local_cache = {}
        if not self._local_cache:
            # Seed with default vehicle (Honda Civic 2022) so user has an active vehicle out-of-the-box
            default_id = "veh-honda-civic-2022"
            self._local_cache[default_id] = {
                "id": default_id,
                "user_id": "default_user",
                "make": "Honda",
                "model": "Civic",
                "year": 2022,
                "fuel_type": "Petrol",
                "engine_variant": "1.5L VTEC Turbo",
                "nickname": "Daily Sedan",
                "odometer": 45000,
                "is_default": True,
                "metadata": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save_local_store()

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
                    return [VehicleOut(**row) for row in res.data]
            except Exception as e:
                logger.warning("Supabase vehicles fetch failed: %s. Falling back to local store.", e)

        # Fallback
        user_vehs = [v for v in self._local_cache.values() if v.get("user_id") == user_id]
        if not user_vehs and self._local_cache:
            user_vehs = list(self._local_cache.values())
        return [VehicleOut(**v) for v in user_vehs]

    def get_vehicle(self, vehicle_id: str) -> Optional[VehicleOut]:
        if self._supabase is not None:
            try:
                res = self._supabase.table("vehicles").select("*").eq("id", vehicle_id).execute()
                if res.data:
                    return VehicleOut(**res.data[0])
            except Exception as e:
                logger.warning("Supabase vehicle get failed: %s", e)

        v = self._local_cache.get(vehicle_id)
        return VehicleOut(**v) if v else None

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

        # If set as default, reset other defaults
        if data.get("is_default"):
            for v in self._local_cache.values():
                if v.get("user_id") == user_id:
                    v["is_default"] = False

        if self._supabase is not None:
            try:
                if data.get("is_default"):
                    self._supabase.table("vehicles").update({"is_default": False}).eq("user_id", user_id).execute()
                res = self._supabase.table("vehicles").insert(data).execute()
                if res.data:
                    created = res.data[0]
                    self._local_cache[created["id"]] = created
                    self._save_local_store()
                    return VehicleOut(**created)
            except Exception as e:
                logger.warning("Supabase vehicle insert failed: %s. Using local store.", e)

        self._local_cache[new_id] = data
        self._save_local_store()
        return VehicleOut(**data)

    def update_vehicle(self, vehicle_id: str, updates: VehicleUpdate, user_id: str = "default_user") -> Optional[VehicleOut]:
        existing = self.get_vehicle(vehicle_id)
        if not existing:
            return None

        update_dict = updates.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        if update_dict.get("is_default"):
            for v in self._local_cache.values():
                if v.get("user_id") == user_id:
                    v["is_default"] = False

        if self._supabase is not None:
            try:
                if update_dict.get("is_default"):
                    self._supabase.table("vehicles").update({"is_default": False}).eq("user_id", user_id).execute()
                res = self._supabase.table("vehicles").update(update_dict).eq("id", vehicle_id).execute()
                if res.data:
                    updated = res.data[0]
                    self._local_cache[vehicle_id] = updated
                    self._save_local_store()
                    return VehicleOut(**updated)
            except Exception as e:
                logger.warning("Supabase vehicle update failed: %s", e)

        data = self._local_cache.get(vehicle_id, existing.model_dump())
        data.update(update_dict)
        self._local_cache[vehicle_id] = data
        self._save_local_store()
        return VehicleOut(**data)

    def delete_vehicle(self, vehicle_id: str) -> bool:
        if self._supabase is not None:
            try:
                self._supabase.table("vehicles").delete().eq("id", vehicle_id).execute()
            except Exception as e:
                logger.warning("Supabase vehicle delete failed: %s", e)

        if vehicle_id in self._local_cache:
            del self._local_cache[vehicle_id]
            self._save_local_store()
            return True
        return False


_vehicle_service_instance = None


def get_vehicle_service() -> VehicleService:
    global _vehicle_service_instance
    if _vehicle_service_instance is None:
        _vehicle_service_instance = VehicleService()
    return _vehicle_service_instance
