"""API tests for audit and reporting endpoints."""

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


def _create_user(email, role, password="Password123!"):
    mig = create_engine(MIGRATOR_URL)
    uid = uuid.uuid4()
    with mig.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, role, is_active) "
                "VALUES (:id, :email, :hp, :role, TRUE)"
            ),
            {"id": uid, "email": email, "hp": hash_password(password), "role": role},
        )
    return uid, email, password


def _login(client, email, password):
    return client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]


@pytest.fixture(scope="module", autouse=True)
def _clean():
    mig = create_engine(MIGRATOR_URL)
    with mig.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE ledger_entries, refused_operations, admin_audit_events, "
                "financial_transactions, idempotency_records, revoked_tokens, accounts, "
                "users CASCADE"
            )
        )
        for acct_type, number in [
            ("SYSTEM_CLEARING_DEPOSIT", "SYS-DEPOSIT"),
            ("SYSTEM_CLEARING_WITHDRAWAL", "SYS-WITHDRAWAL"),
        ]:
            conn.execute(
                text(
                    "INSERT INTO accounts (id, account_number, account_type, currency, status) "
                    "VALUES (gen_random_uuid(), :num, :t, 'INR', 'ACTIVE')"
                ),
                {"num": number, "t": acct_type},
            )
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin():
    uid, email, pw = _create_user(f"admin-{uuid.uuid4()}@example.com", "ADMINISTRATOR")
    c = TestClient(app)
    tok = _login(c, email, pw)
    return {"id": uid, "email": email, "token": tok}


@pytest.fixture
def auditor():
    uid, email, pw = _create_user(f"aud-{uuid.uuid4()}@example.com", "AUDITOR")
    c = TestClient(app)
    tok = _login(c, email, pw)
    return {"id": uid, "email": email, "token": tok}


@pytest.fixture
def holder():
    uid, email, pw = _create_user(f"h-{uuid.uuid4()}@example.com", "ACCOUNT_HOLDER")
    mig = create_engine(MIGRATOR_URL)
    aid = uuid.uuid4()
    with mig.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO accounts (id, account_number, user_id, account_type, currency, "
                "status, projected_balance_paise) VALUES (:id, :num, :uid, 'CUSTOMER', 'INR', "
                "'ACTIVE', 0)"
            ),
            {"id": aid, "num": f"ACC-{aid.hex[:8]}", "uid": uid},
        )
    c = TestClient(app)
    tok = _login(c, email, pw)
    return {"id": uid, "email": email, "token": tok, "account_id": aid}


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_holder_forbidden_audit_events(client, holder):
    r = client.get("/api/audit/events", headers=H(holder["token"]))
    assert r.status_code == 403


def test_holder_forbidden_reconciliation(client, holder):
    r = client.get("/api/audit/reconciliation", headers=H(holder["token"]))
    assert r.status_code == 403


def test_holder_forbidden_clearing(client, holder):
    r = client.get("/api/audit/clearing-balances", headers=H(holder["token"]))
    assert r.status_code == 403


def test_auditor_can_reconcile(client, auditor):
    r = client.get("/api/audit/reconciliation", headers=H(auditor["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["issue_count"] == 0


def test_admin_can_reconcile(client, admin):
    r = client.get("/api/audit/reconciliation", headers=H(admin["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auditor_can_list_events(client, admin, auditor):
    # trigger an audit event via freeze? use admin to freeze not needed; just call events
    r = client.get("/api/audit/events", headers=H(auditor["token"]))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_auditor_can_clearing_balances(client, auditor):
    r = client.get("/api/audit/clearing-balances", headers=H(auditor["token"]))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_reconciliation_detects_no_issues_after_activity(client, admin, holder):
    # make a deposit
    key = str(uuid.uuid4())
    client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    r = client.get("/api/audit/reconciliation", headers=H(admin["token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["issue_count"] == 0


def test_unauthenticated_rejected(client):
    r = client.get("/api/audit/reconciliation")
    assert r.status_code == 401
