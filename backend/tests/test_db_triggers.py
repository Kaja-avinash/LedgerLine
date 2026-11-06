"""Database-level trigger tests (restricted app role).

Verifies that append-only and immutability triggers are enforced by PostgreSQL
itself, not by application code. Tests connect as the restricted
``ledgerline_app`` role and assert that UPDATE/DELETE on protected tables raise.
"""

import os
import uuid
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, OperationalError

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

assert MIGRATOR_URL, "Migrator database URL not configured"
assert APP_URL, "App database URL not configured"


@pytest.fixture(scope="module")
def seeded_ledger_entry():
    """Seed a valid closed financial transaction with two postings as migrator."""
    migrator = create_engine(MIGRATOR_URL)
    user_id = uuid.uuid4()
    customer_account_id = uuid.uuid4()
    clearing_account_id = uuid.uuid4()
    txn_id = uuid.uuid4()
    entry_ids = [uuid.uuid4(), uuid.uuid4()]

    with migrator.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, role, is_active) "
                "VALUES (:id, :email, :hp, 'ACCOUNT_HOLDER', TRUE)"
            ),
            {"id": user_id, "email": f"trigger-{user_id}@test.local", "hp": "x"},
        )
        conn.execute(
            text(
                "INSERT INTO accounts (id, account_number, user_id, account_type, currency, status) "
                "VALUES (:id, :num, :uid, 'CUSTOMER', 'INR', 'ACTIVE')"
            ),
            {"id": customer_account_id, "num": f"CUST-{customer_account_id.hex[:8]}", "uid": user_id},
        )
        conn.execute(
            text(
                "INSERT INTO accounts (id, account_number, account_type, currency, status) "
                "VALUES (:id, :num, 'SYSTEM_CLEARING_DEPOSIT', 'INR', 'ACTIVE')"
            ),
            {"id": clearing_account_id, "num": f"CLR-{clearing_account_id.hex[:8]}"},
        )
        conn.execute(
            text(
                "INSERT INTO financial_transactions "
                "(id, transaction_type, initiator_user_id, reference_id, description, "
                "metadata, is_closed, posted_at) "
                "VALUES (:id, 'DEPOSIT', :uid, :ref, 'trigger seed', '{}'::jsonb, FALSE, NULL)"
            ),
            {"id": txn_id, "uid": user_id, "ref": f"REF-{txn_id}"},
        )
        # postings while unclosed (parent guard allows)
        conn.execute(
            text(
                "INSERT INTO ledger_entries (id, transaction_id, account_id, entry_type, "
                "amount_paise, account_activity_sequence, running_balance_paise) "
                "VALUES (:id, :tid, :aid, 'DEBIT', 1000, 1, 0)"
            ),
            {"id": entry_ids[0], "tid": txn_id, "aid": clearing_account_id},
        )
        conn.execute(
            text(
                "INSERT INTO ledger_entries (id, transaction_id, account_id, entry_type, "
                "amount_paise, account_activity_sequence, running_balance_paise) "
                "VALUES (:id, :tid, :aid, 'CREDIT', 1000, 1, 1000)"
            ),
            {"id": entry_ids[1], "tid": txn_id, "aid": customer_account_id},
        )
        # close the transaction (header protection allows FALSE -> TRUE)
        conn.execute(
            text(
                "UPDATE financial_transactions SET is_closed = TRUE, posted_at = now() "
                "WHERE id = :id"
            ),
            {"id": txn_id},
        )
        # deferred trigger validates at commit

    yield {"entry_ids": entry_ids, "txn_id": txn_id}

    # No cleanup: append-only tables cannot be deleted by design.


@pytest.fixture(scope="module")
def app_engine():
    return create_engine(APP_URL)


def _assert_blocked(exc: Exception) -> None:
    msg = str(exc).lower()
    assert "immutability violation" in msg or "permission denied" in msg or "trigger" in msg, (
        f"Expected immutability trigger to block the operation, got: {exc}"
    )


def test_ledger_entry_update_blocked(seeded_ledger_entry, app_engine):
    entry_id = seeded_ledger_entry["entry_ids"][0]
    with app_engine.connect() as conn:
        with pytest.raises((DBAPIError, OperationalError)) as ei:
            conn.execute(
                text("UPDATE ledger_entries SET amount_paise = 999 WHERE id = :id"),
                {"id": entry_id},
            )
            conn.commit()
        _assert_blocked(ei.value)


def test_ledger_entry_delete_blocked(seeded_ledger_entry, app_engine):
    entry_id = seeded_ledger_entry["entry_ids"][1]
    with app_engine.connect() as conn:
        with pytest.raises((DBAPIError, OperationalError)) as ei:
            conn.execute(
                text("DELETE FROM ledger_entries WHERE id = :id"),
                {"id": entry_id},
            )
            conn.commit()
        _assert_blocked(ei.value)


def test_admin_audit_event_insert_and_protect(app_engine, seeded_ledger_entry):
    """admin_audit_events is append-only: UPDATE/DELETE blocked by trigger."""
    audit_id = uuid.uuid4()
    user_id = seeded_ledger_entry and None
    # Insert as migrator (app lacks... actually app has INSERT via default privs)
    mig = create_engine(MIGRATOR_URL)
    with mig.begin() as conn:
        # need a real user; reuse by inserting one
        uid = uuid.uuid4()
        conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, role, is_active) "
                "VALUES (:id, :email, :hp, 'ADMINISTRATOR', TRUE)"
            ),
            {"id": uid, "email": f"audit-{uid}@test.local", "hp": "x"},
        )
        conn.execute(
            text(
                "INSERT INTO admin_audit_events (id, admin_user_id, action_type, "
                "target_resource_id, reason_narrative) "
                "VALUES (:id, :uid, 'FREEZE_ACCOUNT', :tid, 'test')"
            ),
            {"id": audit_id, "uid": uid, "tid": uuid.uuid4()},
        )

    with app_engine.connect() as conn:
        with pytest.raises((DBAPIError, OperationalError)) as ei:
            conn.execute(
                text("UPDATE admin_audit_events SET action_type = 'X' WHERE id = :id"),
                {"id": audit_id},
            )
            conn.commit()
        _assert_blocked(ei.value)
    with app_engine.connect() as conn:
        with pytest.raises((DBAPIError, OperationalError)) as ei:
            conn.execute(
                text("DELETE FROM admin_audit_events WHERE id = :id"),
                {"id": audit_id},
            )
            conn.commit()
        _assert_blocked(ei.value)
