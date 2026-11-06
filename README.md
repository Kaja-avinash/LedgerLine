# LedgerLine

**Money movement with a ledger you can prove.**

LedgerLine is an enterprise-grade financial transaction management platform built for institutional-grade reliability, concurrency safety, and auditable monetary conservation. It enables administrators, account holders, and compliance auditors to execute deposits, withdrawals, and internal transfers while enforcing double-entry conservation, atomic transaction processing, exact-once idempotency, deterministic row-level concurrency locking, role-based authorization, and an independently verifiable financial ledger.

- **Industry domain:** FinTech
- **Primary technical domain:** Backend systems engineering & Enterprise Web Application
- **Specializations:** Cybersecurity, database engineering, distributed systems, financial transaction processing, double-entry accounting/ledger systems, API engineering, real-time analytics UI.

---

## Architecture & Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Backend** | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.x (Synchronous), Alembic | High-performance synchronous REST API with strict domain separation and data contracts |
| **DB Driver** | `psycopg` 3 (Synchronous) | Native PostgreSQL driver executed in FastAPI threadpool |
| **Database** | PostgreSQL 15+ (developed & verified on 18.6) | Real relational database with DDL triggers, table-level constraints, and privilege separation |
| **Auth** | PyJWT, `pwdlib[argon2]` | Argon2id password hashing, two-step OTP verification, JWT access tokens with database revocation |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons | Tier-one dark-mode enterprise dashboard, interactive SVG balance trend charts, telemetry tickers, and export tools |
| **Testing** | pytest, pytest-asyncio, HTTPX, real PostgreSQL | 54 integration, concurrency, and trigger tests (never SQLite) |

---

## Core Financial & Security Invariants

1. **Integer Money Only (`BIGINT`):** All monetary values are denominated exclusively in integer paise (1 INR = 100 paise) and stored as PostgreSQL `BIGINT`. Floating-point math is completely eliminated across the platform.
2. **Double-Entry Balance Conservation:** For every completed transaction:
   $$\sum \text{Debits} = \sum \text{Credits}$$
   Transactions require a minimum of 2 postings. External funds are balanced against dedicated system clearing accounts (`SYSTEM_CLEARING_DEPOSIT` and `SYSTEM_CLEARING_WITHDRAWAL`).
3. **Deterministic Row-Level Concurrency Locking:** Racing transactions identify affected account UUIDs, deduplicate, and sort ascending before acquiring `SELECT ... FOR UPDATE` locks with a bounded 5s timeout (`SET LOCAL lock_timeout = '5s'`). This eliminates application-level deadlocks and guarantees zero overdrafts under concurrent requests.
4. **Exact-Once Idempotency Engine:** Client requests supply an `Idempotency-Key` header. Requests are claimed atomically via `INSERT ... ON CONFLICT DO NOTHING`. A SHA-256 canonical hash of the request prevents payload tampering. Identical replays return cached responses with identical status codes without re-executing transactions.
5. **Append-Only Tamper Resistance:** PostgreSQL triggers block any `UPDATE` or `DELETE` operations on `ledger_entries`, `refused_operations`, `admin_audit_events`, and finalized `idempotency_records`. Transaction headers transition strictly `FALSE -> TRUE` and cannot be reopened.
6. **Role-Based Access Control (RBAC):**
   - **Administrator:** Account creation, freeze/unfreeze, system ledger inspection, 4-way reconciliation reporting, and compensating reversals with mandatory reason narratives.
   - **Account Holder:** Access restricted to owned accounts, balances, chronological statements, simulated deposits/withdrawals, and transfers.
   - **Auditor:** Read-only access across system-wide ledger entries, audit trails, and reconciliation summaries. State mutation attempts are blocked with HTTP 403 Forbidden.

---

## Repository Structure

```
LedgerLine/
├── backend/
│   ├── alembic/            # Migrations & PostgreSQL trigger definitions
│   ├── app/
│   │   ├── api/            # API routers (auth, users, accounts, transactions, audit)
│   │   ├── core/           # Config, security, database session, email/SMTP, dependencies
│   │   ├── models/         # SQLAlchemy ORM models (8 core financial & audit tables)
│   │   ├── repositories/   # Database access helpers
│   │   ├── schemas/        # Pydantic v2 request/response schemas
│   │   └── services/       # FinancialService, IdempotencyService, ReconciliationService
│   └── tests/              # Pytest integration, concurrency, and trigger test suites
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios API client & typed endpoints
│   │   ├── components/     # Layout, UI library (Card, Button, Modal, Badge), charts
│   │   ├── context/        # AuthContext, ToastContext
│   │   └── pages/          # Dashboard, AdminPanel, Audit, Login, Register
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docs/                   # database_setup.sql, API & architecture docs
├── AGENTS.md               # Master architectural instructions & rules
├── README.md               # Project overview & run instructions
├── THREATS.md              # Threat register & concurrency trade-off analysis
├── PROMPTS.md              # Chronological AI prompt log & human corrections
└── .gitignore
```

---

## Quick Start & Setup Guide

### Prerequisites
- Python 3.13+ (in a dedicated virtual environment `.venv`)
- Node.js 18+ and npm
- PostgreSQL 15+ (tested on PostgreSQL 18.6)
- Git

---

### 1. Database Initialization

Execute the database provisioning script as a PostgreSQL superuser (e.g., `postgres`):

```bash
psql -U postgres -f docs/database_setup.sql
```

This creates:
- Database: `ledgerline_dev`
- Role `ledgerline_migrator`: Schema owner for running Alembic migrations (DDL)
- Role `ledgerline_app`: Restricted runtime role for FastAPI (DML only, no schema modification rights)

---

### 2. Backend Setup

1. Create and activate a Python 3.13 virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Ensure `DATABASE_URL_MIGRATOR`, `DATABASE_URL_APP`, and `JWT_SECRET_KEY` are configured.

4. Apply database migrations and trigger functions:
   ```bash
   cd backend
   alembic upgrade head
   ```

5. Launch the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Healthcheck: `GET http://localhost:8000/health`
   - Interactive Swagger API Documentation: `http://localhost:8000/docs`

---

### 3. Frontend Setup

1. Open a new terminal and navigate to `frontend`:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The UI will be available at: `http://localhost:5173`

---

## Demo Credentials & Seed Accounts

The development environment is pre-seeded with clean, reconciled accounts for each role:

| Role | Email | Password | Account Number | Initial Balance | Capabilities |
|---|---|---|---|---|---|
| **Administrator** | `iamkarao@gmail.com` | `Admin@1234` | N/A (Admin) | N/A | Full ledger inspection, user management, account freeze/unfreeze, 4-way reconciliation, compensating reversals |
| **Account Holder** | `avinashkaja280@gmail.com` | `User@1234` | `ACC-AVINASH01` | ₹0.00 | Simulated deposits, withdrawals, internal transfers, chronological statement export, idempotency inspector |
| **Auditor** | Register / seed with role `AUDITOR` | Password123! | N/A | N/A | Read-only ledger view, audit trail inspection, reconciliation reporting |

*Note: In development mode, OTP codes are logged directly to the backend terminal if live SMTP is not active.*

---

## Running the Automated Test Suite

LedgerLine runs all concurrency, idempotency, and financial integrity tests against **real PostgreSQL** (never SQLite).

```bash
# Run the complete test suite (54 tests):
pytest backend/tests -v
```

### Specific Test Modules:
```bash
# Concurrency stress tests & overdraft racing:
pytest backend/tests/test_financial_service.py -v

# Database triggers & append-only immutability tests:
pytest backend/tests/test_db_triggers.py -v

# Idempotency replay & financial API endpoints:
pytest backend/tests/test_api_financial.py -v

# RBAC, statements, and 4-way reconciliation:
pytest backend/tests/test_api_audit.py -v

# Argon2 password hashing, OTP, and token revocation:
pytest backend/tests/test_api_auth.py -v
```

---

## Frontend Highlights & Visual Analytics

- **Immersive Dark Theme:** Deep midnight aesthetic (`bg-slate-950`) designed to enterprise fin-tech standards.
- **Interactive Balance Analytics:** Dynamic SVG trend chart with interactive time-range filter toggles (`7D`, `30D`, `90D`, `ALL`).
- **Cash Flow Ratio Indicator:** Visual ratio progress bar comparing total credits (inflows) against debits (outflows).
- **Idempotency Inspector Modal:** Transparent verification tool displaying client idempotency keys, fingerprints, and cached execution states.
- **Account Freeze / Unfreeze Modals:** Administrative confirmation modals for freezing and unfreezing customer accounts.
- **Statement Export:** Real-time CSV export and print-ready formal bank statement views with activity sequences.
- **Toast Notification System:** Animated slide-in toasts for feedback across all authentication and transaction operations.

---

## License

Built for individual engineering assessment (Snovasys). Private repository.
