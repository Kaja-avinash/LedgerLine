# LedgerLine

**Money movement with a ledger you can prove.**

LedgerLine is a secure financial transaction management platform built for an
individual engineering assessment (Snovasys). It enables administrators and
account holders to manage accounts, perform deposits, withdrawals and internal
transfers while preserving monetary conservation, atomic transaction processing,
idempotency, concurrency safety, account-level authorization and an
independently traceable financial ledger.

- **Industry domain:** FinTech
- **Primary technical domain:** Backend systems engineering
- **Specializations:** Cybersecurity, database engineering, distributed systems,
  financial transaction processing, accounting/ledger systems, API engineering,
  application security

## Implemented Features

- Authentication with three roles: Administrator, Account Holder, Auditor.
- JWT (PyJWT) with Argon2 (pwdlib) password hashing and token revocation.
- Role-based and resource-level authorization (defense-in-depth).
- Account creation, listing (permission-scoped), details, balances.
- Simulated deposits and withdrawals, internal transfers.
- Double-entry ledger with balanced postings (debits = credits).
- Integer paise (BIGINT) monetary values — no floating point.
- Atomic early idempotency claim with SHA-256 request fingerprints.
- Deterministic global account locking (`SELECT ... FOR UPDATE` in UUID order).
- Per-account monotonic activity sequence for statements.
- Refused-operation audit with observed balances.
- Full transaction reversals (admin-only, reason required, balance checks).
- Append-only ledger/audit tables enforced by PostgreSQL triggers.
- Deferred constraint triggers (transaction closure, balance equality,
  idempotency terminal state).
- Read-only 4-way reconciliation engine.
- Admin audit events and security audit separation.
- Automated tests: conservation, concurrency, idempotency, authorization,
  ledger integrity, DB trigger enforcement.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.x (sync), Alembic |
| DB driver | psycopg 3 (synchronous) |
| Database | PostgreSQL 15+ (developed/tested on 18.6) |
| Auth | PyJWT, pwdlib (Argon2) |
| Frontend (planned) | React 18, TypeScript, Vite, Tailwind CSS |
| Testing | pytest, pytest-asyncio, HTTPX, real PostgreSQL |

## Architecture Overview

```
backend/
  app/
    api/        # routers: auth, users, accounts, transactions, audit
    core/       # config, security, database, deps
    models/     # SQLAlchemy ORM (8 core tables)
    schemas/    # Pydantic v2 request/response
    services/   # FinancialService, ReconciliationService
  alembic/     # migrations + triggers
  tests/       # pytest (real PostgreSQL)
frontend/      # (planned)
docs/          # database_setup.sql
reference/     # architecture reference (read-only)
```

Financial invariants are enforced at **both** application and database level
(deferred constraint triggers, append-only triggers, row-level locks).

## Setup

### Prerequisites

- Python 3.13+
- PostgreSQL 15+ (local or managed)
- Git

### 1. Clone

```bash
git clone https://github.com/Kaja-avinash/LedgerLine.git
cd LedgerLine
```

### 2. Python environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Database setup

Run as a PostgreSQL superuser (e.g. `postgres`) the script
`docs/database_setup.sql` after replacing the placeholder passwords. It creates:

- Database `ledgerline_dev`
- Role `ledgerline_migrator` (schema owner)
- Role `ledgerline_app` (restricted runtime)

Then copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

Required variables: `DATABASE_URL_MIGRATOR`, `DATABASE_URL_APP` (or the
`DB_*` component variables), `JWT_SECRET_KEY`.

### 4. Migrations

```bash
cd backend
alembic upgrade head
```

### 5. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `GET http://localhost:8000/health`

Interactive API docs: `http://localhost:8000/docs`

## Running Tests

Tests run against a **real PostgreSQL** instance (not SQLite).

```bash
cd backend
pytest -q
```

Run a specific suite:

```bash
pytest tests/test_db_triggers.py -v
pytest tests/test_financial_service.py -v
pytest tests/test_api_financial.py -v
pytest tests/test_api_audit.py -v
```

## API Documentation (summary)

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | public | Register account holder |
| POST | /api/auth/login | public | Obtain JWT |
| POST | /api/auth/logout | bearer | Revoke token |
| GET | /api/auth/me | bearer | Current user |
| POST | /api/users | admin | Create user |
| GET | /api/users | admin | List users |
| GET/PATCH | /api/users/{id} | admin/self | Get/update user |
| GET | /api/accounts | bearer | List accounts (scoped) |
| GET | /api/accounts/{id} | bearer | Account details |
| POST | /api/accounts | admin | Create account |
| POST | /api/accounts/{id}/freeze | admin | Freeze account |
| POST | /api/accounts/{id}/unfreeze | admin | Unfreeze account |
| GET | /api/accounts/{id}/statement | bearer | Per-account statement |
| POST | /api/transactions/deposit | holder | Simulated deposit (Idempotency-Key) |
| POST | /api/transactions/withdraw | holder | Simulated withdrawal (Idempotency-Key) |
| POST | /api/transactions/transfer | holder | Internal transfer (Idempotency-Key) |
| POST | /api/transactions/{id}/reverse | admin | Full reversal (Idempotency-Key) |
| GET | /api/audit/events | admin/auditor | Admin audit events |
| GET | /api/audit/clearing-balances | admin/auditor | System clearing balances |
| GET | /api/audit/reconciliation | admin/auditor | Read-only reconciliation report |

All money-moving requests require an `Idempotency-Key` header.

## Security Highlights

- Argon2 password hashing, JWT with expiry and revocation table.
- Defense-in-depth authorization (router + service layer).
- Account ownership verified on every request; no IDOR.
- Deterministic row-level locking prevents concurrent overdrafts/deadlocks.
- Append-only ledger/audit tables enforced by PostgreSQL triggers.
- Restricted runtime DB role cannot alter schema or historical records.

## Known Limitations

- Frontend (React dashboards) not yet built.
- Deployment not yet performed.
- Only INR supported; no external payment gateway (simulated).
- Full reversals only (no partial reversals).

## Implementation Status

Milestones 1–4 complete (foundation, schema/triggers, auth, financial engine,
API routes, audit/reporting). Frontend and deployment pending.

## License

Individual assessment project — not licensed for redistribution.
