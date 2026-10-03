import logging
from typing import Optional
from supabase import create_client, Client
from backend.app.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client(admin: bool = False) -> Client:
    """
    Returns a configured Supabase client.
    
    If admin=True, uses the SUPABASE_SERVICE_ROLE_KEY if available for
    administrative ingestion operations. Otherwise, uses SUPABASE_KEY.
    """
    global _supabase_client, _supabase_admin_client

    if not settings.supabase_url:
        raise ValueError(
            "SUPABASE_URL is not set. Please configure your .env file with your "
            "Supabase project URL."
        )

    if admin:
        if _supabase_admin_client is not None:
            return _supabase_admin_client

        key = settings.supabase_service_role_key or settings.supabase_key
        if not key:
            raise ValueError(
                "Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_KEY is configured. "
                "Please configure credentials in your .env file."
            )
        _supabase_admin_client = create_client(settings.supabase_url, key)
        return _supabase_admin_client
    else:
        if _supabase_client is not None:
            return _supabase_client

        key = settings.supabase_key or settings.supabase_service_role_key
        if not key:
            raise ValueError(
                "SUPABASE_KEY is not configured. Please configure credentials in your .env file."
            )
        _supabase_client = create_client(settings.supabase_url, key)
        return _supabase_client
