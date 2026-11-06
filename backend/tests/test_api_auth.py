"""API tests for authentication and user management (OTP flow)."""

import io
import contextlib
import re
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import login_and_get_token

client = TestClient(app)


def _register(email, password="Password123!", role="ACCOUNT_HOLDER"):
    return client.post("/api/auth/register", json={"email": email, "password": password, "role": role})


def test_register_account_holder():
    email = f"holder-{uuid.uuid4()}@example.com"
    r = _register(email)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == email
    assert body["role"] == "ACCOUNT_HOLDER"
    assert body["is_active"] is True


def test_register_privileged_role_rejected():
    email = f"bad-{uuid.uuid4()}@example.com"
    r = _register(email, role="ADMINISTRATOR")
    assert r.status_code == 403


def test_register_duplicate_email():
    email = f"dup-{uuid.uuid4()}@example.com"
    r1 = _register(email)
    assert r1.status_code == 201
    r2 = _register(email)
    assert r2.status_code == 409


def test_login_success():
    email = f"login-{uuid.uuid4()}@example.com"
    _register(email)
    # step 1: login returns otp_required
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": "Password123!", "role": "ACCOUNT_HOLDER"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "otp_required"
    assert r.json()["email"] == email
    # step 2: verify otp -> token
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r1 = client.post(
            "/api/auth/login",
            data={"username": email, "password": "Password123!", "role": "ACCOUNT_HOLDER"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    m = re.search(r"OTP for .*?: (\d{6})", buf.getvalue())
    otp = m.group(1)
    r2 = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    assert r2.status_code == 200, r2.text
    assert "access_token" in r2.json()


def test_login_wrong_password():
    email = f"login2-{uuid.uuid4()}@example.com"
    _register(email)
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": "wrong", "role": "ACCOUNT_HOLDER"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_login_role_mismatch():
    email = f"login3-{uuid.uuid4()}@example.com"
    _register(email)
    # account holder trying admin login
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": "Password123!", "role": "ADMINISTRATOR"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_me_authenticated():
    email = f"me-{uuid.uuid4()}@example.com"
    _register(email)
    token = login_and_get_token(client, email, "Password123!")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_me_unauthenticated():
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_logout_revokes_token():
    email = f"lo-{uuid.uuid4()}@example.com"
    _register(email)
    token = login_and_get_token(client, email, "Password123!")
    r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401


def test_verify_otp_invalid():
    email = f"otp-{uuid.uuid4()}@example.com"
    _register(email)
    client.post(
        "/api/auth/login",
        data={"username": email, "password": "Password123!", "role": "ACCOUNT_HOLDER"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    r = client.post("/api/auth/verify-otp", json={"email": email, "otp": "000000"})
    assert r.status_code == 401


def test_verify_otp_expired_or_missing():
    r = client.post("/api/auth/verify-otp", json={"email": "nobody@example.com", "otp": "123456"})
    assert r.status_code == 401
