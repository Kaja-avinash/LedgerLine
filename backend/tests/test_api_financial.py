"""API tests for financial operations."""

import os
import uuid
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.main import app
from tests.conftest import login_and_get_token
from app.models.user import User

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


def _ensure_system_accounts():
    mig = create_engine(MIGRATOR_URL)
    with mig.begin() as conn:
        for acct_type, number in [
            ("SYSTEM_CLEARING_DEPOSIT", "SYS-DEPOSIT"),
            ("SYSTEM_CLEARING_WITHDRAWAL", "SYS-WITHDRAWAL"),
        ]:
            exists = conn.execute(
                text("SELECT 1 FROM accounts WHERE account_type = :t"), {"t": acct_type}
            ).fetchone()
            if not exists:
                conn.execute(
                    text(
                        "INSERT INTO accounts (id, account_number, account_type, currency, status) "
                        "VALUES (gen_random_uuid(), :num, :t, 'INR', 'ACTIVE')"
                    ),
                    {"num": number, "t": acct_type},
                )


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


def _create_account(user_id, balance=0):
    mig = create_engine(MIGRATOR_URL)
    aid = uuid.uuid4()
    with mig.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO accounts (id, account_number, user_id, account_type, currency, "
                "status, projected_balance_paise) VALUES (:id, :num, :uid, 'CUSTOMER', 'INR', "
                "'ACTIVE', :bal)"
            ),
            {"id": aid, "num": f"ACC-{aid.hex[:8]}", "uid": user_id, "bal": balance},
        )
    return aid


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
    _ensure_system_accounts()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def holder():
    _ensure_system_accounts()
    uid, email, pw = _create_user(f"h-{uuid.uuid4()}@example.com", "ACCOUNT_HOLDER")
    aid = _create_account(uid, balance=50000)
    c = TestClient(app)
    tok = login_and_get_token(c, email, pw)
    return {"id": uid, "email": email, "password": pw, "account_id": aid, "token": tok}


@pytest.fixture
def holder2():
    _ensure_system_accounts()
    uid, email, pw = _create_user(f"h2-{uuid.uuid4()}@example.com", "ACCOUNT_HOLDER")
    aid = _create_account(uid, balance=10000)
    c = TestClient(app)
    tok = login_and_get_token(c, email, pw)
    return {"id": uid, "email": email, "password": pw, "account_id": aid, "token": tok}


@pytest.fixture
def auditor():
    _ensure_system_accounts()
    uid, email, pw = _create_user(f"aud-{uuid.uuid4()}@example.com", "AUDITOR")
    c = TestClient(app)
    tok = login_and_get_token(c, email, pw, role="AUDITOR")
    return {"id": uid, "email": email, "password": pw, "token": tok}


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_deposit_success(client, holder):
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 5000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert body["new_balance_paise"] == 55000


def test_deposit_missing_idempotency_key(client, holder):
    r = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers=H(holder["token"]),
    )
    assert r.status_code == 400


def test_deposit_idempotency_replay(client, holder):
    key = str(uuid.uuid4())
    r1 = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r1.status_code == 200
    tid = r1.json()["transaction_id"]
    r2 = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r2.status_code == 200
    assert r2.json()["transaction_id"] == tid


def test_deposit_idempotency_payload_mismatch(client, holder):
    key = str(uuid.uuid4())
    r1 = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r1.status_code == 200
    r2 = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 2000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r2.status_code == 422


def test_withdraw_insufficient_funds(client, holder):
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/withdraw",
        json={"account_id": str(holder["account_id"]), "amount_paise": 999999},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "INSUFFICIENT_FUNDS"


def test_transfer_success(client, holder, holder2):
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/transfer",
        json={
            "from_account_id": str(holder["account_id"]),
            "to_account_id": str(holder2["account_id"]),
            "amount_paise": 5000,
        },
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "COMPLETED"
    assert body["source_new_balance_paise"] == 45000
    assert body["destination_new_balance_paise"] == 15000


def test_transfer_self_rejected(client, holder):
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/transfer",
        json={
            "from_account_id": str(holder["account_id"]),
            "to_account_id": str(holder["account_id"]),
            "amount_paise": 100,
        },
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "SELF_TRANSFER"


def test_holder_cannot_deposit_into_others_account(client, holder, holder2):
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder2["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    # holder2's account not owned by holder -> 404
    assert r.status_code == 404


def test_auditor_cannot_deposit(client, auditor, holder):
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(auditor["token"]), "Idempotency-Key": key},
    )
    # auditor is authenticated but not the owner -> 403 (forbidden) from service
    assert r.status_code == 403


def test_list_accounts_role_scoping(client, holder, holder2):
    # holder sees only own
    r = client.get("/api/accounts", headers=H(holder["token"]))
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()]
    assert str(holder["account_id"]) in ids
    assert str(holder2["account_id"]) not in ids


def test_statement_endpoint(client, holder):
    # make a deposit first
    key = str(uuid.uuid4())
    client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    r = client.get(f"/api/accounts/{holder['account_id']}/statement", headers=H(holder["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["account_id"] == str(holder["account_id"])
    assert len(body["items"]) >= 1


def test_reverse_requires_admin(client, holder):
    # create a deposit transaction first
    key = str(uuid.uuid4())
    r = client.post(
        "/api/transactions/deposit",
        json={"account_id": str(holder["account_id"]), "amount_paise": 1000},
        headers={**H(holder["token"]), "Idempotency-Key": key},
    )
    tid = r.json()["transaction_id"]
    # holder attempting reverse -> 403 (not admin)
    r2 = client.post(
        f"/api/transactions/{tid}/reverse",
        json={"reason": "test"},
        headers={**H(holder["token"]), "Idempotency-Key": str(uuid.uuid4())},
    )
    assert r2.status_code == 403
