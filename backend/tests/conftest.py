"""Shared pytest fixtures and helpers for LedgerLine tests."""

import contextlib
import io
import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


def login_and_get_token(client: TestClient, email: str, password: str, role: str = "ACCOUNT_HOLDER") -> str:
    """Perform the two-step OTP login and return the JWT access token."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = client.post(
            "/api/auth/login",
            data={"username": email, "password": password, "role": role},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "otp_required"
    out = buf.getvalue()
    m = re.search(r"OTP for .*?: (\d{6})", out)
    assert m, f"OTP not found in output: {out}"
    otp = m.group(1)

    r2 = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    assert r2.status_code == 200, r2.text
    return r2.json()["access_token"]
