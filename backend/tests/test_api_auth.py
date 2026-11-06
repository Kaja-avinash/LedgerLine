"""API tests for authentication and user management."""

import os
import uuid
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.security import hash_password
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)


def _build_url(prefix: str) -> str | None:
    user = os.getenv(f"DB_{prefix}_USER")
    if not user:
        return None
    password = os.getenv(f"DB_{prefix}_PASSWORD", "")
    host = os.getenv(f"DB_{prefix}_HOST", "localhost")
    port = os.getenv(f"DB_{prefix}_PORT", "5432")
    name = os.getenv(f"DB_{prefix}_NAME", "ledgerline_dev")
    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


MIGRATOR_URL = _build_url("MIGRATOR") or os.getenv("DATABASE_URL_MIGRATOR")
APP_URL = _build_url("APP") or os.getenv("DATABASE_URL_APP")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin user via migrator and return a bearer token."""
    mig = create_engine(MIGRATOR_URL)
    uid = uuid.uuid4()
    email = f"admin-{uid}@example.com"
    password = "AdminPass123!"
    with mig.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, role, is_active) "
                "VALUES (:id, :email, :hp, 'ADMINISTRATOR', TRUE)"
            ),
            {"id": uid, "email": email, "hp": hash_password(password)},
        )
    # login via API to get token
    c = TestClient(app)
    r = c.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"], email


def test_register_account_holder(client):
    email = f"holder-{uuid.uuid4()}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!", "role": "ACCOUNT_HOLDER"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == email
    assert body["role"] == "ACCOUNT_HOLDER"
    assert body["is_active"] is True


def test_register_privileged_role_rejected(client):
    email = f"bad-{uuid.uuid4()}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!", "role": "ADMINISTRATOR"},
    )
    assert r.status_code == 403


def test_register_duplicate_email(client):
    email = f"dup-{uuid.uuid4()}@example.com"
    r1 = client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    assert r1.status_code == 201
    r2 = client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    assert r2.status_code == 409


def test_login_success(client):
    email = f"login-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    r = client.post("/api/auth/login", data={"username": email, "password": "Password123!"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    email = f"login2-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    r = client.post("/api/auth/login", data={"username": email, "password": "wrong"})
    assert r.status_code == 401


def test_me_authenticated(client):
    email = f"me-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_logout_revokes_token(client):
    email = f"lo-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
    r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 204
    # token now revoked
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 401


def test_admin_create_user(admin_token):
    token, _ = admin_token
    email = f"created-{uuid.uuid4()}@example.com"
    r = TestClient(app).post(
        "/api/users",
        json={"email": email, "password": "Password123!", "role": "AUDITOR"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "AUDITOR"


def test_admin_list_users_requires_admin(client):
    email = f"holder-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
    r = client.get("/api/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_holder_cannot_view_other_user(client, admin_token):
    # create a second holder
    email = f"h2-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
    tok2 = client.post("/api/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
    # get its id
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok2}"}).json()
    # another holder
    email3 = f"h3-{uuid.uuid4()}@example.com"
    client.post("/api/auth/register", json={"email": email3, "password": "Password123!"})
    tok3 = client.post("/api/auth/login", data={"username": email3, "password": "Password123!"}).json()["access_token"]
    # tok3 tries to view tok2's user -> 403
    r = client.get(f"/api/users/{me['id']}", headers={"Authorization": f"Bearer {tok3}"})
    assert r.status_code == 403
