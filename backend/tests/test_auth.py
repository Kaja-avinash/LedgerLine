"""Tests for authentication utilities (password hashing, JWT, RBAC helpers)."""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest

from app.core import security
from app.core.deps import has_role
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_wrong_password_fails():
    hashed = hash_password("secret")
    assert verify_password("not-secret", hashed) is False


def test_verify_invalid_hash_returns_false():
    assert verify_password("anything", "not-a-valid-hash") is False


def test_create_and_decode_token():
    uid = uuid.uuid4()
    token, jti, expires_at = create_access_token(uid, "ACCOUNT_HOLDER")
    assert isinstance(token, str) and token
    assert jti
    payload = decode_access_token(token)
    assert payload["sub"] == str(uid)
    assert payload["role"] == "ACCOUNT_HOLDER"
    assert payload["jti"] == jti
    assert "exp" in payload


def test_expired_token_rejected():
    from app.core.config import settings

    payload = {
        "sub": str(uuid.uuid4()),
        "role": "ACCOUNT_HOLDER",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token)


def test_tampered_token_rejected():
    uid = uuid.uuid4()
    token, _, _ = create_access_token(uid, "ACCOUNT_HOLDER")
    # tamper the signature
    tampered = token[:-4] + "AAAA"
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_has_role_allows():
    user = SimpleNamespace(role="ADMINISTRATOR")
    assert has_role(user, "ADMINISTRATOR") is True
    assert has_role(user, "ADMINISTRATOR", "AUDITOR") is True


def test_has_role_denies():
    user = SimpleNamespace(role="ACCOUNT_HOLDER")
    assert has_role(user, "ADMINISTRATOR") is False
    assert has_role(user, "AUDITOR") is False
    assert has_role(user, "ADMINISTRATOR", "AUDITOR") is False
