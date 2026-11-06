"""Security utilities: password hashing (Argon2) and JWT (PyJWT)."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# Argon2 password hasher (pwdlib).
_password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2."""
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    try:
        return _password_hasher.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, str, datetime]:
    """Create a signed JWT access token.

    Returns (token, jti, expires_at).
    """
    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return token, jti, expires_at


ALLOWED_ALGORITHMS = ["HS256"]


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure."""
    # Reject algorithm confusion (e.g. "none").
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise
    if header.get("alg") not in ALLOWED_ALGORITHMS:
        raise jwt.InvalidAlgorithmError("Unsupported JWT algorithm")
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=ALLOWED_ALGORITHMS,
    )
