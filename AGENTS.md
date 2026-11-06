# AGENTS.md — LedgerLine

> Persistent project-instruction file for OpenCode. Read and follow this before any development task.
> Last updated: 2026-11-06. Update when approved architectural decisions change.

## 1. Project Identity

- **Name:** LedgerLine
- **Tagline:** Money movement with a ledger you can prove.
- **Domain:** FinTech — secure financial transaction management.
- **Assessment:** Individual engineering assessment (Snovasys). AI tools permitted; must be individually defensible.
- **Deadline:** 12 Nov 2026, 6:00 PM IST.
- **Primary objective:** Build a financially correct, secure, concurrency-safe, independently verifiable system.

## 2. Primary Objective (Non-Negotiable)

Move money so the books always balance and the same request never pays twice. The system must remain correct under:
- simultaneous financial operations,
- replayed requests (network timeouts, double-clicks),
- manipulated account/user identifiers,
- unauthorized access attempts,
- mid-transaction database failures,
- simultaneous withdrawals,
- attempts to modify historical ledger records.

This is a financial-integrity and concurrency challenge, not a CRUD app.

## 3. Approved Technology Stack

- **Language:** Python 3.13 (use `.venv`; never global installs).
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2.x (synchronous), Alembic.
- **DB driver:** `psycopg[binary]` v3 (synchronous). Normal sync route handlers in threadpool; never block in async functions.
- **Database:** PostgreSQL 15+ (local dev/test on PostgreSQL 18.6; managed PG for deploy).
- **Auth:** `PyJWT` (JWT) + `pwdlib[argon2]` (Argon2 password hashing). Do NOT use python-jose / passlib[bcrypt].
- **Frontend (later):** React 18, TypeScript, Vite, Tailwind CSS.
- **Testing:** pytest, pytest-asyncio, HTTPX, real PostgreSQL (never SQLite for locking/concurrency).
- **No Docker** unless a specific deployment/reproducibility requirement justifies it (not approved for initial dev).

## 4. Repository & Git Workflow

- Branch: `main`. Remote: `origin` = `https://github.com/Kaja-avinash/LedgerLine.git` (private).
- Commit after each logically complete, tested milestone. Push automatically to `origin/main` after verification.
- Commit messages: `feat(...)`, `fix(...)`, `test(...)`, `docs(...)`, `chore(...)`.
- Never force-push, rewrite history, backdate, delete branches, or change visibility without explicit approval.
- Never commit secrets, `.env`, `.venv`, `node_modules`, temp files, or incomplete critical financial code.
- Run relevant tests, review diff, scan for secrets before every commit/push. Verify push present on remote.
- Repository stays **private** throughout development. Visibility change requires explicit approval after placement-cell clarification.

## 5. Folder Structure

```
LedgerLine/
├── backend/
│   ├── app/
│   │   ├── api/            # routers (auth, accounts, transactions, statements, admin, audit, reconcile)
│   │   ├── core/           # config, security, deps, db session, roles
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic v2 request/response
│   │   ├── services/       # financial engine, idempotency, locking, reversals, reconciliation
│   │   └── repositories/   # DB access helpers
│   ├── alembic/            # migrations + triggers
│   └── tests/              # unit + integration (real PG) + concurrency
├── frontend/               # React 18 / TS / Vite / Tailwind (later milestone)
├── docs/                   # API, DB, threat, prompts
├── reference/              # architecture reference (read-only input)
├── AGENTS.md
├── README.md
├── THREATS.md
├── PROMPTS.md
└── .gitignore
```

## 6. Financial Invariants (MUST HOLD ALWAYS)

1. **Integer money only.** All monetary values are integer paise stored as `BIGINT`. INR only (reject other currencies). No floats anywhere. Reject zero, negative, invalid precision.
2. **Double-entry balance.** For every completed transaction: `SUM(DEBIT) == SUM(CREDIT)`. Minimum 2 postings.
3. **Conservation.** `Total closing customer balances = Total opening + Net deposits − Net withdrawals`. Internal transfers net zero. Reversals reflected in net deposits/withdrawals.
4. **No negative customer balances.** `CHECK (account_type != 'CUSTOMER' OR projected_balance_paise >= 0)`.
5. **No unrestricted adjustment account.** Customer balances change only via documented external deposits/withdrawals and authorized compensating reversals.
6. **Atomicity.** All financial changes (header, postings, balances, activity sequence, idempotency result) commit together or roll back together.

## 7. Accounting Model

- `CUSTOMER` — platform liability, credit-normal, `Balance = Credits − Debits`, non-negative.
- `SYSTEM_CLEARING_DEPOSIT` — asset, debit-normal, `Balance = Debits − Credits`.
- `SYSTEM_CLEARING_WITHDRAWAL` — liability, credit-normal, `Balance = Credits − Debits`.

Postings:
- Deposit: debit `SYSTEM_CLEARING_DEPOSIT`, credit customer.
- Withdrawal: debit customer, credit `SYSTEM_CLEARING_WITHDRAWAL`.
- Transfer: debit source, credit destination.
- Reversal: new transaction referencing original; invert every posting (same accounts/amounts).

## 8. Transaction Header Lifecycle

1. Create unclosed header (`is_closed = FALSE`).
2. Acquire all required account locks (deterministic order).
3. Validate account states and balances.
4. Insert balanced ledger postings.
5. Update projected balances + activity sequences.
6. Transition header `FALSE -> TRUE` exactly once; set `posted_at`.
7. Store final idempotency response.
8. Commit after deferred DB validation succeeds.

After closure: do not modify original attributes, reopen, change initiator, description/metadata, or append postings.

## 9. Concurrency & Locking Rules

- For every financial operation: identify affected accounts → dedup → sort UUIDs ascending → `SELECT ... FOR UPDATE` in that order → validate after lock → mutate within transaction.
- Include system clearing accounts whenever their projected balances change.
- Use READ COMMITTED + explicit row locks.
- Bounded retry on PG error `40P01` (deadlock) with jitter (max 3). For ambiguous commit outcomes, resolve via idempotency record — never blindly replay the money movement.
- Deterministic ordering prevents application deadlocks; DB-internal deadlocks still possible → retry.

## 10. Idempotency Rules

- Atomic early claim inside the same transaction: `INSERT ... ON CONFLICT (user_id, key) DO NOTHING RETURNING user_id, key`.
- Fingerprint = SHA-256 over canonical JSON of {user, method, endpoint, payload, source, dest, amount, currency, ...}.
- Claimed → proceed. Exists → verify fingerprint → return cached response if identical; HTTP 422 if payload differs; no mutation.
- Concurrent identical requests wait for competing transaction; on commit retrieve cached response; on rollback retry can claim.
- Final status must be `COMPLETED` or `REFUSED` before commit. Never committed `IN_PROGRESS`.
- Deferred validation queries the live idempotency row. Completed/refused records protected from ordinary UPDATE/DELETE.

## 11. Reversal Rules

- Only completed original can be reversed; reversal cannot itself be reversed; at most one full reversal per original (partial unique index on `reverses_transaction_id`).
- Exact inverted postings for same accounts/amounts.
- Check every customer account debited by the reversal for adequate balance (reversing a transfer may debit the recipient).
- Reject reversals that would create negative customer balances.
- Require administrator + mandatory reason narrative.
- Protect reversal requests with idempotency.

## 12. Authentication & Authorization

- JWT (PyJWT): verify signature, expiry, active user, revocation (revoked_tokens table: JTI, user, expiry, revocation time, reason).
- Logout/admin revocation invalidates token.
- RBAC + resource-level ownership on every request. Financial service re-checks inside transaction (ownership, status, classification, currency, eligibility, balance, self-transfer prohibition).
- Role matrix:
  - **Administrator:** user/account management, account creation, freeze/unfreeze, ledger inspection, reconciliation, authorized reversals with reason. Denied: unrestricted customer deposits/withdrawals/transfers, impersonation.
  - **Account Holder:** own accounts only — balances, statements, permitted simulated deposits/withdrawals, transfers from owned accounts. Denied: other users' accounts, role/ownership changes, ledger edits.
  - **Auditor:** read-only system-wide statements, ledger, refusals, reconciliation. Denied: all mutations, account management, role changes, ledger modifications, deletions.
- Public registration never permits self-assignment of Administrator or Auditor.

## 13. Security Requirements

Analyze and mitigate: auth failures, password compromise, session/token attacks, broken access control, BOLA/IDOR, privilege escalation, account/user ID manipulation, replay, idempotency abuse, race conditions, double-spending, SQL injection, invalid financial inputs, mass assignment, CSRF (where applicable), CORS misconfiguration, sensitive info exposure, ledger/audit tampering, excessive login attempts, DB privilege abuse, unsafe retries, dependency vulnerabilities, secret exposure.

Separate audit storage: financial transactions, ledger postings, idempotency records, refused operations, admin audit events, security audit events, token revocation records, account activity events.

Unauthorized attempts logged in `admin_audit_events` (security audit) without disclosing target account balances or private activity. Do not misrepresent an account holder as an administrator.

Secrets never committed. Use env vars + `.env` (gitignored). Never external-directory access without explicit approval.

## 14. Database Security & Role Separation

- **Migration/schema-owner role:** owns schema, manages migrations, triggers, DB objects.
- **Restricted runtime app role:** DML only; does not own financial tables; cannot disable triggers, alter schema, remove immutability protections, or modify/delete historical ledger/audit records.
- Database superusers are outside the app security boundary.
- Append-only triggers on `ledger_entries`, `refused_operations`, `admin_audit_events` (and completed/refused idempotency records) reject UPDATE/DELETE.

## 15. Audit & Statements

- Every statement shows: successful debits/credits, refused attempts, running balances, initiating user, transaction IDs, timestamps, activity sequence, descriptions, statuses.
- Refused attempts traceable without being a successful posting.
- Unauthorized attempts recorded separately (security audit) without leaking target-account info.
- Statements order by `account_activity_sequence`, not timestamps.
- Running balance stored on refused attempts (`observed_balance_paise`).

## 16. Reconciliation (Read-Only)

Verify: customer balances = Credits − Debits; deposit clearing = Debits − Credits; withdrawal clearing = Credits − Debits; every transaction balanced; projected = ledger-derived; internal transfers conserve; reversals compensate; platform conservation holds. Never modify historical records to force reconciliation.

## 17. Testing Expectations

Real PostgreSQL only for locking/concurrency. Independent DB sessions + realistic synchronization (asyncio.Barrier / threading). Tests must genuinely fail if a protection is removed. Required suites: conservation, concurrent overdraft (10×₹800 on ₹1000 → 1 success/9 refusals/₹200), identical idempotency (5× same key → 1 transfer), opposing transfers (20 concurrent, no deadlock), authorization (cross-user, IDOR, auditor writes, admin withdrawals), ledger integrity (UPDATE/DELETE rejection, posting to closed, unbalanced, duplicate reversal), idempotency integrity (replay, payload mutation, rollback recovery, no committed IN_PROGRESS), failure injection, audit/statements, DB security under runtime role.

## 18. Documentation Responsibilities

Maintain at repo root: `README.md`, `AGENTS.md`, `THREATS.md`, `PROMPTS.md`, API docs, DB docs (schema, migrations, seed, role setup, reconciliation). `THREATS.md`: genuine threat register with ID, scenario, impact, component, mitigation, test, evidence, remaining risk, status. `PROMPTS.md`: ≥5 dated genuine entries (≥2 financial/concurrency/idempotency, ≥2 authz/audit), each with date, tool/model, prompt/task, generated output, what was wrong/risky, how identified, correction, commit link. Never fabricate.

## 19. Deployment Restrictions

- Keep repo private until explicit approval. Deploy only after local tests pass.
- Provide safe demo credentials for all 3 roles; isolated demo data; no production secrets.
- Verify deployed app end-to-end (auth, RBAC, ownership, deposits, withdrawals, transfers, replays, concurrency, statements, audit, errors).

## 20. Prohibited Operations (Never Without Explicit Approval)

- Force push, history rewriting, backdating, concealing commits, branch deletion, repo deletion, remote reconfiguration, visibility changes, publishing publicly.
- Modifying global OpenCode config; using `--auto`/unrestricted auto-approval.
- Accessing unrelated external directories without approval.
- Installing dependencies globally (use `.venv`).
- Introducing ML training/datasets/AI auto-money-movement.

## 21. Conflict Resolution Note

The reference document (`reference/LedgerLine_Final_Architecture_Validation.docx`) uses async SQLAlchemy/asyncpg examples in some sections. Per approved decisions, this project uses **synchronous** psycopg 3 + sync SQLAlchemy + sync route handlers. The master instructions and the user's subsequent corrections take precedence. Flag any further conflicts rather than silently choosing.

## 22. Code Standards

- Readable code, robust error handling, explicit transaction boundaries in service layer.
- No financial logic in routers. Routers parse/validate/delegate; services mutate.
- Defense-in-depth: router RBAC + resource ownership AND service-layer re-checks inside transaction.
- All financial mutation through `FinancialService` only.
- Type hints, Pydantic v2 schemas, Alembic migrations for all schema changes.
- Tests exercise real backend + PostgreSQL behavior.
