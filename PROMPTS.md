# PROMPTS.md — LedgerLine AI Usage Documentation

Genuine record of AI-assisted development using OpenCode with the selected model
**Beam Free — Reflection Beam 1.0 501B A23B**. Entries below include cases where
the AI produced confident but unsafe code that would have moved real money
incorrectly; the human reviewer caught and corrected each one. No fabricated
mistakes, prompts, dates, tests, or commit links.

---

## Entry 1 — 2026-11-05 (AI wrong: naive idempotency would double-pay)

- **Date:** 2026-11-05
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** "Implement idempotency for the transfer endpoint so a retried request does not pay twice."
- **What the model generated:** A check-then-act pattern: `SELECT 1 FROM idempotency_records WHERE key = :k`; if absent, run the transfer, then `INSERT` the record. The model stated this was "safe for retries."
- **What was wrong or risky:** The check and the insert were separate statements with no unique constraint enforcement at claim time. Two concurrent identical requests could both pass the `SELECT`, both execute the transfer, and both insert — resulting in a double payment. This would have moved real money incorrectly.
- **How identified:** Human review flagged the TOCTOU race and the missing atomic claim; cross-checked against PostgreSQL READ COMMITTED semantics.
- **Correction:** Rejected the generated code. Required an atomic early claim: `INSERT INTO idempotency_records (...) ON CONFLICT (user_id, key) DO NOTHING RETURNING user_id, key` as the first statement inside the transaction, with a composite primary key and a deferred terminal-state trigger. Implemented in `FinancialService._claim_key`.
- **Commit link:** `e55a2d3` (Milestone 4 engine).

## Entry 2 — 2026-11-05 (AI wrong: missing row locks would allow concurrent overdraft)

- **Date:** 2026-11-05
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** "Implement a withdrawal: check balance, then decrement."
- **What the model generated:** `if account.balance >= amount: account.balance -= amount` with no `SELECT ... FOR UPDATE`, relying on application-level reads under READ COMMITTED.
- **What was wrong or risky:** Under concurrency, two withdrawals could both read the same balance and both succeed, driving the account negative (overdraft / money creation). This would have moved real money incorrectly.
- **How identified:** Human review identified the missing row lock and the lost-update anomaly; referenced the master requirement for atomic balance checks.
- **Correction:** Rejected the generated code. Required deterministic global locking: deduplicate affected account UUIDs, sort ascending, acquire `SELECT ... FOR UPDATE` in that order, re-check balance after locking, and mutate within the transaction. Implemented in `FinancialService._lock_accounts`.
- **Commit link:** `e55a2d3` (Milestone 4 engine).

## Entry 3 — 2026-11-06 (AI wrong: idempotency ignored payload tampering)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** "Handle idempotency replay: if the key exists, return the cached response."
- **What the model generated:** Replay handler that returned the cached response whenever the key existed, without comparing the request payload.
- **What was wrong or risky:** An attacker could reuse a key with a different amount/recipient and receive the original (or, worse, trigger a second movement). This would have allowed fraudulent money movement.
- **How identified:** Human review flagged the missing fingerprint comparison against the master spec requirement.
- **Correction:** Rejected the generated code. Required a SHA-256 fingerprint over canonical JSON of {user, method, endpoint, payload, source, dest, amount, currency}; mismatch returns HTTP 422 with no mutation. Implemented in `FinancialService._fingerprint` and `_verify_replay`.
- **Commit link:** `e55a2d3` (Milestone 4 engine).

## Entry 4 — 2026-11-06 (AI wrong: floating-point money)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** "Define the account balance column and amount fields."
- **What the model generated:** `balance: float` / `Numeric(18, 2)` with Python `float` arithmetic for totals.
- **What was wrong or risky:** Floating-point representation would introduce rounding errors that accumulate across postings, breaking conservation (money created/lost at the penny level).
- **How identified:** Human review against the master instruction "never use floating-point arithmetic for money."
- **Correction:** Rejected the generated code. Required integer paise stored as `BIGINT`, INR only, with `CHECK` constraints and no floats anywhere.
- **Commit link:** `71f79d7` (Milestone 2 schema).

## Entry 5 — 2026-11-06 (AI wrong: unrestricted adjustment account)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** "Add a system adjustment account for admin corrections."
- **What the model generated:** A `SYSTEM_ADJUSTMENT` account with no constraints, allowing arbitrary credits/debits to customer balances.
- **What was wrong or risky:** Would let an administrator silently inflate/deflate customer balances, violating conservation.
- **How identified:** Human review against the chart-of-accounts rule (no unrestricted adjustment account).
- **Correction:** Rejected the generated code. Required the documented three-account model (CUSTOMER, SYSTEM_CLEARING_DEPOSIT, SYSTEM_CLEARING_WITHDRAWAL) with customer balances changing only via documented deposits/withdrawals/reversals.
- **Commit link:** `71f79d7` (Milestone 2 schema).

## Entry 6 — 2026-11-05 (AI wrong: Python version / auth libraries)

- **Date:** 2026-11-05
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Initial environment inspection and stack recommendation.
- **What the model generated:** Proposed using the detected Python 3.10.11 and the already-installed `python-jose` / `passlib[bcrypt]`.
- **What was wrong or risky:** Python 3.10 reached EOL on 2026-10-01; `python-jose`/`passlib` are less maintained than the specified alternatives.
- **How identified:** User review of the assessment against the master instructions.
- **Correction:** User directed Python 3.13.17, `PyJWT`, and `pwdlib[argon2]`. Documented in AGENTS.md §3.
- **Commit link:** N/A (pre-implementation).

## Entry 7 — 2026-11-06 (AI wrong: async vs sync)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Reconcile the reference architecture document with the master instructions.
- **What the model generated:** Reference snippets using async SQLAlchemy/asyncpg; initial assessment treated them as authoritative.
- **What was wrong or risky:** Adopting async would conflict with the approved synchronous stack and complicate real-PostgreSQL concurrency testing.
- **How identified:** Cross-checking against the master instruction's approved stack and the user's explicit sync decision.
- **Correction:** Synchronous psycopg 3 + SQLAlchemy + sync route handlers take precedence; documented in AGENTS.md §21.
- **Commit link:** N/A (documentation).

## Entry 8 — 2026-11-06 (AI wrong: trigger stale NEW row image)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Implement the deferred transaction-closure trigger.
- **What the model generated:** A deferred trigger reading `NEW.is_closed` from the INSERT event image.
- **What was wrong or risky:** When a header is inserted as unclosed then updated to closed in the same transaction, the deferred trigger would see the stale `NEW` image (is_closed = FALSE) and reject valid commits.
- **How identified:** Reference document's explicit warning about stale `NEW` row images.
- **Correction:** Trigger queries the live row by primary key at COMMIT time (`SELECT is_closed FROM financial_transactions WHERE id = NEW.id`).
- **Commit link:** `71f79d7` (Milestone 2 schema).

## Entry 9 — 2026-11-06 (AI wrong: idempotency URL configparser %)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Configure Alembic to read the migrator DB URL from the environment.
- **What the model generated:** `config.set_main_option("sqlalchemy.url", url)` with the URL containing URL-encoded passwords (e.g. `%40`).
- **What was wrong or risky:** configparser's default interpolation interpreted `%` and raised `ValueError: invalid interpolation syntax`, breaking all migrations.
- **How identified:** `alembic current` failure.
- **Correction:** Resolve URL in `env.py` and pass directly to `create_engine`/`context.configure`, bypassing configparser; also added component-based env vars with auto-encoding.
- **Commit link:** `5d47f6b` (Milestone 1 DB).

## Entry 10 — 2026-11-06 (AI wrong: concurrency test hang)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Write concurrency stress tests using `threading.Barrier`.
- **What the model generated:** 20-thread barrier synchronization in `test_opposing_transfers_no_deadlock`.
- **What was wrong or risky:** If any worker failed before reaching the barrier, the barrier broke and all 20 threads hung indefinitely, freezing the suite.
- **How identified:** Test run hung; required manual process kill.
- **Correction:** Removed barrier synchronization; ThreadPoolExecutor provides sufficient concurrency without hang risk.
- **Commit link:** `e55a2d3` (Milestone 4 engine).

## Entry 11 — 2026-11-06 (AI wrong: account_number length / server defaults)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Seed test accounts in trigger tests.
- **What the model generated:** `account_number = f"CUST-{uuid}"` (40 chars) into a `VARCHAR(32)` column; models with Python-side defaults only.
- **What was wrong or risky:** `StringDataRightTruncation` on insert; raw inserts missing NOT NULL columns failed.
- **How identified:** Pytest failures (`value too long`, `NotNullViolation`).
- **Correction:** Shortened account numbers; added `server_default` to all defaulted columns in models and migration.
- **Commit link:** `71f79d7` (Milestone 2 schema).

## Entry 12 — 2026-11-06 (AI wrong: migrator CONNECT privilege)

- **Date:** 2026-11-06
- **AI tool used:** OpenCode (Beam Free).
- **Prompt / task:** Generate the DB setup SQL with role separation.
- **What the model generated:** Revoked `CONNECT` from `PUBLIC` and granted it only to `ledgerline_app`, assuming the owner retains it automatically.
- **What was wrong or risky:** The migrator role (not owner in all setups) lost `CONNECT` and could not run migrations.
- **How identified:** `alembic current` failed with "permission denied for database".
- **Correction:** Added `GRANT ALL ON DATABASE ledgerline_dev TO ledgerline_migrator;`.
- **Commit link:** `5d47f6b` (Milestone 1 DB).


## Entry 13 — 2026-11-06 (AI wrong: Frontend routing race condition on login)

- **Date:** 2026-11-06
- **AI tool used:** Antigravity / Gemini 2.5.
- **Prompt / task:** "Resolve UI routing bug where user logs in, header updates with user info, but page remains stuck on login form."
- **What the model generated:** Set user state in AuthContext, but did not guard the public `/login` route or redirect authenticated users visiting root `/`.
- **What was wrong or risky:** Users completing OTP verification remained stranded on the login form unless they manually typed `/dashboard` in the address bar.
- **How identified:** User testing of the authentication flow.
- **Correction:** Implemented `PublicRoute` wrapper that automatically redirects authenticated users to `/dashboard`, added immediate imperative navigation upon successful OTP verification in `Login.tsx`, and ensured `App.tsx` routes properly guard unauthenticated vs authenticated views.
- **Commit link:** Milestone 5 (Frontend UI/UX).

## Entry 14 — 2026-11-06 (AI wrong: Password visibility toggle inverted)

- **Date:** 2026-11-06
- **AI tool used:** Antigravity / Gemini 2.5.
- **Prompt / task:** "Fix password visibility toggle in Login and Register components."
- **What the model generated:** Rendered `Eye` when `type="password"` (hidden) and `EyeOff` when `type="text"` (visible).
- **What was wrong or risky:** UX convention inversion: users saw an open eye while their password was obscured as dots and a crossed-out eye when their password was in cleartext.
- **How identified:** User testing of password input fields on Login and Register forms.
- **Correction:** Inverted the conditional rendering across `Login.tsx` and `Register.tsx` to `{showPassword ? <Eye className="w-4 h-4"/> : <EyeOff className="w-4 h-4"/>}` so the icon indicates current visibility state accurately.
- **Commit link:** Milestone 5 (Frontend UI/UX).

## Entry 15 — 2026-11-06 (AI wrong: Rigid self-ownership check blocked administrative funding)

- **Date:** 2026-11-06
- **AI tool used:** Antigravity / Gemini 2.5.
- **Prompt / task:** "Fix 403 Forbidden error when Administrator attempts to deposit funds into a user's account for testing."
- **What the model generated:** `if customer.user_id != initiator.id: raise FinancialError("FORBIDDEN", ...)` strictly requiring the logged-in user to be the account owner for deposits and withdrawals.
- **What was wrong or risky:** Platform administrators could not deposit funds or simulate capital movements into customer accounts for operational or testing purposes.
- **How identified:** User attempted an admin-initiated test deposit and encountered a 403 error.
- **Correction:** Updated authorization logic in `FinancialService` to permit the action if `customer.user_id == initiator.id or initiator.role == "ADMINISTRATOR"`. Cross-customer transfers between account holders remain strictly blocked, and all admin-initiated adjustments are immutably logged to `admin_audit_events`.
- **Commit link:** Milestone 5 (Financial Engine & Admin Bypass).

## Entry 16 — 2026-11-06 (AI wrong: Test fixtures failed when live SMTP credentials configured)

- **Date:** 2026-11-06
- **AI tool used:** Antigravity / Gemini 2.5.
- **Prompt / task:** "Execute backend automated test suite against PostgreSQL."
- **What the model generated:** Tests used `login_and_get_token` fixture expecting `[dev] OTP for ...` printed to stdout, while `send_otp_email` dispatched real emails via Gmail SMTP when SMTP env vars were populated.
- **What was wrong or risky:** When live SMTP credentials were added to `.env`, `send_email` attempted network delivery to synthetic `@example.com` addresses, skipping the stdout print. The test fixture regex failed, causing test errors across `test_api_audit.py`.
- **How identified:** Pytest fixture errors during test execution.
- **Correction:** Added synthetic domain detection in `send_email`: if `PYTEST_CURRENT_TEST` is set or `to.endswith("@example.com")`, SMTP network delivery is skipped and OTP fallback logging occurs immediately. 54 of 54 tests passed.
- **Commit link:** Milestone 5 (Test Suite Hardening).
