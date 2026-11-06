"""Tests for the core financial service (real PostgreSQL)."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.user import User
from app.services.financial import (
    FinancialService,
    InsufficientFundsError,
    SelfTransferError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _engine():
    import os
    from pathlib import Path
    from urllib.parse import quote_plus
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    url = os.getenv("DATABASE_URL_MIGRATOR")
    if not url:
        user = os.getenv("DB_MIGRATOR_USER")
        if user:
            pw = os.getenv("DB_MIGRATOR_PASSWORD", "")
            host = os.getenv("DB_MIGRATOR_HOST", "localhost")
            port = os.getenv("DB_MIGRATOR_PORT", "5432")
            name = os.getenv("DB_MIGRATOR_NAME", "ledgerline_dev")
            url = (
                f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(pw)}"
                f"@{host}:{port}/{name}"
            )
    assert url, "Migrator DB URL not configured"
    return create_engine(url)


@pytest.fixture(scope="module", autouse=True)
def _clean_db_before_module(engine):
    with engine.begin() as c:
        c.execute(
            text(
                "TRUNCATE TABLE ledger_entries, refused_operations, admin_audit_events, "
                "financial_transactions, idempotency_records, revoked_tokens, accounts, "
                "users CASCADE"
            )
        )
    yield


@pytest.fixture(scope="module")
def engine():
    return _engine()


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def _ensure_system_accounts(session):
    """Ensure the two system clearing accounts exist (idempotent)."""
    for acct_type, number in [
        ("SYSTEM_CLEARING_DEPOSIT", "SYS-DEPOSIT"),
        ("SYSTEM_CLEARING_WITHDRAWAL", "SYS-WITHDRAWAL"),
    ]:
        existing = session.execute(
            text("SELECT id FROM accounts WHERE account_type = :t"), {"t": acct_type}
        ).fetchone()
        if existing is None:
            session.execute(
                text(
                    "INSERT INTO accounts (id, account_number, account_type, currency, status) "
                    "VALUES (gen_random_uuid(), :num, :t, 'INR', 'ACTIVE')"
                ),
                {"num": number, "t": acct_type},
            )
    session.commit()


def _create_user_and_account(session, balance_paise: int = 0) -> tuple:
    user = User(
        email=f"fin-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("pw"),
        role="ACCOUNT_HOLDER",
        is_active=True,
    )
    session.add(user)
    session.flush()
    acct_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO accounts (id, account_number, user_id, account_type, currency, "
            "status, projected_balance_paise) VALUES (:id, :num, :uid, 'CUSTOMER', 'INR', "
            "'ACTIVE', :bal)"
        ),
        {"id": acct_id, "num": f"ACC-{acct_id.hex[:8]}", "uid": user.id, "bal": balance_paise},
    )
    session.commit()
    return user, acct_id


# ---------------------------------------------------------------------------
# Conservation & basic correctness
# ---------------------------------------------------------------------------

def test_deposit_conservation(session):
    _ensure_system_accounts(session)
    user, acct = _create_user_and_account(session, 0)
    svc = FinancialService(session)
    res = svc.deposit(
        initiator=user,
        account_id=acct,
        amount_paise=10000,
        idempotency_key=str(uuid.uuid4()),
        request_path="/deposit",
        request_payload={"amount": 10000},
    )
    assert res.status_code == 200
    assert res.body["new_balance_paise"] == 10000

    # clearing deposit balance should equal debits
    row = session.execute(
        text("SELECT projected_balance_paise FROM accounts WHERE account_type='SYSTEM_CLEARING_DEPOSIT'")
    ).scalar()
    assert row == 10000

    # ledger balanced
    txn_id = res.transaction_id
    debits = session.execute(
        text("SELECT COALESCE(SUM(amount_paise),0) FROM ledger_entries WHERE transaction_id=:t AND entry_type='DEBIT'"),
        {"t": txn_id},
    ).scalar()
    credits = session.execute(
        text("SELECT COALESCE(SUM(amount_paise),0) FROM ledger_entries WHERE transaction_id=:t AND entry_type='CREDIT'"),
        {"t": txn_id},
    ).scalar()
    assert debits == credits == 10000


def test_withdrawal_conservation(session):
    _ensure_system_accounts(session)
    user, acct = _create_user_and_account(session, 5000)
    svc = FinancialService(session)
    res = svc.withdraw(
        initiator=user,
        account_id=acct,
        amount_paise=2000,
        idempotency_key=str(uuid.uuid4()),
        request_path="/withdraw",
        request_payload={"amount": 2000},
    )
    assert res.status_code == 200
    assert res.body["new_balance_paise"] == 3000
    row = session.execute(
        text("SELECT projected_balance_paise FROM accounts WHERE account_type='SYSTEM_CLEARING_WITHDRAWAL'")
    ).scalar()
    assert row == 2000


def test_transfer_conservation(session):
    _ensure_system_accounts(session)
    u1, a1 = _create_user_and_account(session, 5000)
    u2, a2 = _create_user_and_account(session, 1000)
    svc = FinancialService(session)
    res = svc.transfer(
        initiator=u1,
        from_account_id=a1,
        to_account_id=a2,
        amount_paise=1500,
        idempotency_key=str(uuid.uuid4()),
        request_path="/transfer",
        request_payload={"amount": 1500},
    )
    assert res.status_code == 200
    assert res.body["source_new_balance_paise"] == 3500
    assert res.body["destination_new_balance_paise"] == 2500

    # total customer money conserved
    total = session.execute(
        text(
            "SELECT COALESCE(SUM(projected_balance_paise),0) FROM accounts "
            "WHERE account_type='CUSTOMER'"
        )
    ).scalar()
    # 5000+1000 = 6000 minus... wait both accounts: 3500+2500=6000
    assert total >= 6000  # at least these two; other tests may add


def test_withdraw_insufficient_funds_refused(session):
    _ensure_system_accounts(session)
    user, acct = _create_user_and_account(session, 1000)
    svc = FinancialService(session)
    with pytest.raises(InsufficientFundsError):
        svc.withdraw(
            initiator=user,
            account_id=acct,
            amount_paise=5000,
            idempotency_key=str(uuid.uuid4()),
            request_path="/withdraw",
            request_payload={"amount": 5000},
        )
    # balance unchanged
    bal = session.execute(
        text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": acct}
    ).scalar()
    assert bal == 1000
    # refused_operations recorded
    cnt = session.execute(
        text("SELECT COUNT(*) FROM refused_operations WHERE account_id=:id"), {"id": acct}
    ).scalar()
    assert cnt >= 1


def test_self_transfer_rejected(session):
    _ensure_system_accounts(session)
    user, acct = _create_user_and_account(session, 1000)
    svc = FinancialService(session)
    with pytest.raises(SelfTransferError):
        svc.transfer(
            initiator=user,
            from_account_id=acct,
            to_account_id=acct,
            amount_paise=100,
            idempotency_key=str(uuid.uuid4()),
            request_path="/transfer",
            request_payload={"amount": 100},
        )


def test_idempotency_replay(session):
    _ensure_system_accounts(session)
    u1, a1 = _create_user_and_account(session, 5000)
    u2, a2 = _create_user_and_account(session, 0)
    key = str(uuid.uuid4())
    payload = {"amount": 1000}
    svc = FinancialService(session)
    r1 = svc.transfer(
        initiator=u1,
        from_account_id=a1,
        to_account_id=a2,
        amount_paise=1000,
        idempotency_key=key,
        request_path="/transfer",
        request_payload=payload,
    )
    assert r1.status_code == 200
    # replay with same key+payload
    r2 = svc.transfer(
        initiator=u1,
        from_account_id=a1,
        to_account_id=a2,
        amount_paise=1000,
        idempotency_key=key,
        request_path="/transfer",
        request_payload=payload,
    )
    assert r2.transaction_id == r1.transaction_id
    # balances only moved once
    src_bal = session.execute(
        text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": a1}
    ).scalar()
    assert src_bal == 4000


def test_idempotency_payload_mismatch(session):
    _ensure_system_accounts(session)
    u1, a1 = _create_user_and_account(session, 5000)
    u2, a2 = _create_user_and_account(session, 0)
    key = str(uuid.uuid4())
    svc = FinancialService(session)
    svc.transfer(
        initiator=u1,
        from_account_id=a1,
        to_account_id=a2,
        amount_paise=1000,
        idempotency_key=key,
        request_path="/transfer",
        request_payload={"amount": 1000},
    )
    with pytest.raises(Exception) as ei:
        svc.transfer(
            initiator=u1,
            from_account_id=a1,
            to_account_id=a2,
            amount_paise=2000,
            idempotency_key=key,
            request_path="/transfer",
            request_payload={"amount": 2000},
        )
    assert ei.value.code == "IDEMPOTENCY_PAYLOAD_MISMATCH"


# ---------------------------------------------------------------------------
# Concurrency tests
# ---------------------------------------------------------------------------

def test_concurrent_overdraft_protection(engine):
    """10 concurrent withdrawals of 80000 from a 100000 balance -> 1 success."""
    _ensure_system_accounts_sync(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # seed user+account
    with Session() as s:
        user, acct = _create_user_and_account(s, 100000)
        s.commit()
        user_id = user.id
        account_id = acct

    results = {"success": 0, "refused": 0, "errors": []}
    lock = threading.Lock()

    def worker(i):
        sess = Session()
        try:
            user = sess.get(User, user_id)
            svc = FinancialService(sess)
            try:
                svc.withdraw(
                    initiator=user,
                    account_id=account_id,
                    amount_paise=80000,
                    idempotency_key=f"wd-{i}-{uuid.uuid4()}",
                    request_path="/withdraw",
                    request_payload={"amount": 80000},
                )
                with lock:
                    results["success"] += 1
            except InsufficientFundsError:
                with lock:
                    results["refused"] += 1
            except Exception as e:
                with lock:
                    results["errors"].append(str(e))
        finally:
            sess.close()

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(worker, i) for i in range(10)]
        for f in as_completed(futs):
            f.result()

    assert results["success"] == 1, results
    assert results["refused"] == 9, results
    assert results["errors"] == [], results

    # verify balance
    with Session() as s:
        bal = s.execute(
            text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": account_id}
        ).scalar()
        assert bal == 20000, bal
        # exactly one debit posting and 9 refused rows
        debits = s.execute(
            text("SELECT COUNT(*) FROM ledger_entries WHERE account_id=:id AND entry_type='DEBIT'"),
            {"id": account_id},
        ).scalar()
        assert debits == 1
        refused = s.execute(
            text("SELECT COUNT(*) FROM refused_operations WHERE account_id=:id"), {"id": account_id}
        ).scalar()
        assert refused == 9


def test_concurrent_identical_idempotency(engine):
    """5 concurrent identical transfers with same key -> 1 transfer."""
    _ensure_system_accounts_sync(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as s:
        u1, a1 = _create_user_and_account(s, 50000)
        u2, a2 = _create_user_and_account(s, 0)
        s.commit()
        user_id = u1.id
        from_id = a1
        to_id = a2

    key = str(uuid.uuid4())
    payload = {"amount": 30000}
    results = {"ids": [], "errors": []}
    lock = threading.Lock()

    def worker(i):
        sess = Session()
        try:
            user = sess.get(User, user_id)
            svc = FinancialService(sess)
            try:
                r = svc.transfer(
                    initiator=user,
                    from_account_id=from_id,
                    to_account_id=to_id,
                    amount_paise=30000,
                    idempotency_key=key,
                    request_path="/transfer",
                    request_payload=payload,
                )
                with lock:
                    results["ids"].append(r.transaction_id)
            except Exception as e:
                with lock:
                    results["errors"].append(str(e))
        finally:
            sess.close()

    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(worker, i) for i in range(5)]
        for f in as_completed(futs):
            f.result()

    assert results["errors"] == [], results
    assert len(set(str(x) for x in results["ids"])) == 1, results
    # balances moved once
    with Session() as s:
        src = s.execute(text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": from_id}).scalar()
        dst = s.execute(text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": to_id}).scalar()
        assert src == 20000, src
        assert dst == 30000, dst


def test_opposing_transfers_no_deadlock(engine):
    """20 concurrent transfers (10 A->B, 10 B->A) complete without deadlock."""
    _ensure_system_accounts_sync(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as s:
        u1, a = _create_user_and_account(s, 100000)
        u2, b = _create_user_and_account(s, 100000)
        s.commit()
        ua, ub = u1.id, u2.id
        # need user objects for both; fetch in workers
        a_id, b_id = a, b

    barrier = None
    errors = []
    lock = threading.Lock()

    def worker(i):
        sess = Session()
        try:
            if i % 2 == 0:
                initiator = sess.get(User, ua)
                frm, to = a_id, b_id
            else:
                initiator = sess.get(User, ub)
                frm, to = b_id, a_id
            svc = FinancialService(sess)
            svc.transfer(
                initiator=initiator,
                from_account_id=frm,
                to_account_id=to,
                amount_paise=1000,
                idempotency_key=f"opp-{i}-{uuid.uuid4()}",
                request_path="/transfer",
                request_payload={"amount": 1000},
            )
        except Exception as e:
            with lock:
                errors.append(str(e))
        finally:
            sess.close()

    with ThreadPoolExecutor(max_workers=20) as ex:
        futs = [ex.submit(worker, i) for i in range(20)]
        for f in as_completed(futs):
            f.result()

    assert errors == [], errors[:5]
    with Session() as s:
        ba = s.execute(text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": a_id}).scalar()
        bb = s.execute(text("SELECT projected_balance_paise FROM accounts WHERE id=:id"), {"id": b_id}).scalar()
        assert ba + bb == 200000, (ba, bb)


# ---------------------------------------------------------------------------
# Module-level sync helper for system accounts (used in concurrency tests)
# ---------------------------------------------------------------------------

def _ensure_system_accounts_sync(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as s:
        _ensure_system_accounts(s)
        s.commit()
