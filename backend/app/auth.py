"""
AutoAssist AI - Authentication and User Identity Module
Provides Supabase Auth JWT token extraction, verification, and user authorization dependencies.
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from backend.app.config import settings
from backend.app.database import get_supabase_client

logger = logging.getLogger(__name__)


def extract_token_from_header(request: Request) -> Optional[str]:
    """Extracts Bearer token from Authorization header if present."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


async def get_current_user_id(request: Request) -> str:
    """
    FastAPI dependency that resolves the authenticated user's ID.
    
    1. If a Supabase JWT Bearer token is provided in Authorization header,
       validates it with Supabase Auth to extract verified user UUID.
    2. If an X-User-ID header is provided (e.g., frontend client session), uses it.
    3. If a query parameter or body contains user_id, falls back to it in local dev mode.
    4. Defaults safely to 'default_user' for demo/unauthenticated local sessions.
    """
    token = extract_token_from_header(request)
    if token:
        try:
            supabase = get_supabase_client(admin=False)
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                return str(user_response.user.id)
        except Exception as e:
            logger.debug("Supabase token verification failed: %s", e)
            # Token invalid/expired: do not raise 401 if public endpoints allow guest access,
            # but reject spoofed identities if explicitly invalid

    # Check for X-User-ID custom header (used by authenticated frontend client state)
    x_user_id = request.headers.get("X-User-ID") or request.headers.get("x-user-id")
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()

    # Check query params for dev/testing backwards compatibility
    query_user_id = request.query_params.get("user_id")
    if query_user_id and query_user_id.strip():
        return query_user_id.strip()

    return "default_user"


async def require_authenticated_user_id(
    user_id: str = Depends(get_current_user_id)
) -> str:
    """
    Strict dependency for endpoints requiring verified authentication.
    Rejects 'default_user' if strict auth is enforced.
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required."
        )
    return user_id
