# PROMPTS.md — LedgerLine AI Usage Documentation

Genuine record of AI-assisted development using OpenCode with the selected model
**Beam Free — Reflection Beam 1.0 501B A23B**. No fabricated mistakes, prompts,
dates, tests, or commit links.

---

## Entry 1 — 2026-11-05

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Initial repository inspection and engineering assessment of
  LedgerLine requirements; propose architecture, stack, threat model, test
  strategy, Git workflow.
- **What the model generated:** Full initial engineering assessment including
  repository/environment inspection, recommended stack, application architecture,
  database/accounting design, transaction/concurrency strategy, idempotency
  design, authz matrix, threat model, testing strategy, Git/GitHub workflow,
  7-day roadmap, unresolved decisions.
- **What was wrong or risky:** The assessment detected Python 3.10.11 as the
  installed interpreter and proposed using it; Python 3.10 reached EOL on
  2026-10-01. Also referenced `python-jose`/`passlib[bcrypt]` which were already
  installed but are not the preferred maintained libraries.
- **How identified:** User review of the assessment against the master
  instructions (which required Python 3.12+ and specified `PyJWT` +
  `pwdlib[argon2]`).
- **Correction:** User directed use of Python 3.13.17 (downloaded and verified),
  `PyJWT`, and `pwdlib[argon2]`. Documented in AGENTS.md §3.
- **Commit link:** N/A (pre-implementation phase).

## Entry 2 — 2026-11-05

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Reconcile the supplied architecture reference document
  (`LedgerLine_Final_Architecture_Validation.docx`) with the master instructions;
  identify conflicts.
- **What the model generated:** Extraction and analysis of the reference doc's
  schema, triggers, and service snippets; identified that the reference uses
  async SQLAlchemy/asyncpg in some sections while the approved stack is
  synchronous psycopg v3.
- **What was wrong or risky:** Silently adopting the async examples would have
  conflicted with the approved synchronous decision and complicated concurrency
  testing.
- **How identified:** Cross-checking reference snippets against the master
  instruction's approved stack and the user's explicit sync decision.
- **Correction:** AGENTS.md §21 documents that synchronous psycopg 3 +
  SQLAlchemy + sync route handlers take precedence; conflicts flagged rather than
  silently resolved.
- **Commit link:** N/A (documentation).

## Entry 3 — 2026-11-06

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Generate the initial Alembic migration with ORM models and
  inject PostgreSQL triggers (append-only, deferred constraint triggers, parent-row
  lock guard, header protection, idempotency protection).
- **What the model generated:** Migration `42fdb682316d` with 8 tables, constraints,
  partial unique index, and 8 triggers/functions.
- **What was wrong or risky:** (a) Model columns with Python-side defaults lacked
  `server_default`, causing NOT NULL violations on raw inserts in tests.
  (b) The migration's deferred trigger for transaction closure required postings
  to be flushed before `is_closed` was set to TRUE; otherwise the parent-row
  guard blocked them.
- **How identified:** Pytest `test_db_triggers.py` / `test_deposit_conservation`
  failures (`NotNullViolation`, `prevent_posting_to_closed_transaction`).
- **Correction:** Added `server_default` to model columns and migration; added
  `self.db.flush()` before closing the transaction header in
  `FinancialService`.
- **Commit link:** `71f79d7` (Milestone 2 schema).

## Entry 4 — 2026-11-06

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Implement early atomic idempotency claiming and concurrent
  replay handling.
- **What the model generated:** `_claim_key` using `INSERT ... ON CONFLICT DO
  NOTHING RETURNING`; fingerprint via SHA-256 canonical JSON; replay verification
  and payload-mismatch 422.
- **What was wrong or risky:** The Alembic `env.py` injected the migrator URL via
  `config.set_main_option`, which uses configparser interpolation and choked on
  `%` characters in URL-encoded passwords (`invalid interpolation syntax`).
- **How identified:** `alembic current` failed with `ValueError: invalid
  interpolation syntax`.
- **Correction:** `env.py` now resolves the URL from env and passes it directly
  to `create_engine`/`context.configure`, bypassing configparser interpolation.
  Also added component-based env vars with auto-URL-encoding.
- **Commit link:** `5d47f6b` (Milestone 1 DB) and `71f79d7`.

## Entry 5 — 2026-11-06

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Implement deterministic account locking and concurrency
  stress tests.
- **What the model generated:** Locking helper sorting UUIDs ascending with
  `SELECT ... FOR UPDATE`; concurrent overdraft, identical-idempotency, and
  opposing-transfer tests using `threading.Barrier`.
- **What was wrong or risky:** The `threading.Barrier` could hang the whole suite
  if any worker failed before reaching the barrier (broken barrier propagated to
  all). Also, the migrator role initially lacked `CONNECT` privilege on
  `ledgerline_dev` because the SQL script revoked `CONNECT` from `PUBLIC` but
  only granted it to the app role.
- **How identified:** Test suite hung on `test_opposing_transfers_no_deadlock`;
  `alembic current` failed with "permission denied for database".
- **Correction:** Removed barrier synchronization (ThreadPoolExecutor provides
  concurrency); added `GRANT ALL ON DATABASE ledgerline_dev TO
  ledgerline_migrator;` to the setup SQL and a fix-up snippet.
- **Commit link:** `e55a2d3` (Milestone 4 engine) and `5d47f6b`.

## Entry 6 — 2026-11-06

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Build auth API routes (register/login/logout/me) and
  user management with RBAC; write Pytest tests.
- **What the model generated:** Auth routers, schemas, admin user management,
  `test_api_auth.py`.
- **What was wrong or risky:** (a) Test emails used `@test.local`, rejected by
  email-validator 2.3.0 as a reserved/special-use domain. (b) `require_roles`
  was accidentally removed during a `has_role` refactor, causing `NameError`.
- **How identified:** Pytest collection errors (`NameError: name 'require_roles'
  is not defined`) and 422 validation errors on register.
- **Correction:** Re-added `require_roles` factory; changed test emails to
  `@example.com`.
- **Commit link:** `521f42e` (Milestone 3 API).

## Entry 7 — 2026-11-06

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Implement full transaction reversal in the financial engine
  and expose via API.
- **What the model generated:** `FinancialService.reverse` with legality checks,
  exact inverted postings, balance sufficiency for debited customer accounts,
  single-reversal enforcement via partial unique index.
- **What was wrong or risky:** Reversal of a transfer can debit the recipient;
  naive "only deposits need funds" assumption would miss this. Documented in
  AGENTS.md §11.
- **How identified:** Review of reversal posting inversion against the master
  spec §7.10.
- **Correction:** Balance check applied to every customer account debited by the
  reversal, not just deposit reversals.
- **Commit link:** `e3efdfe` (Milestone 4 API).

## Entry 8 — 2026-11-06

- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Implement audit/reporting endpoints and read-only
  reconciliation; update README.
- **What the model generated:** `ReconciliationService` (4-way), audit router
  (events, clearing balances, reconciliation), README with setup/run/test/API/
  security/limitations/status.
- **What was wrong or risky:** None major; verified all 9 audit tests pass and
  reconciliation reports `status: ok` after activity.
- **How identified:** Pytest run (`test_api_audit.py`: 9 passed).
- **Correction:** N/A — validated as-is.
- **Commit link:** `80d94da` (Milestone 5 audit).
