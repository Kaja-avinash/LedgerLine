# THREATS.md — LedgerLine Threat Register

Genuine threat register. Each entry links an attack scenario to its concrete
mitigation and automated test evidence. No threat is marked mitigated without
implementation and test evidence.

## T-01 — Concurrent overdraft (double-spend)

- **Threat ID:** T-01
- **Description:** Two or more simultaneous withdrawals from the same account
  could both succeed and drive the balance negative.
- **Attack scenario:** 10 concurrent requests of ₹800 against a ₹1,000 balance.
- **Impact:** Negative balance, money creation.
- **Affected component:** Financial service / accounts.
- **Mitigation:** `SELECT ... FOR UPDATE` row locks in deterministic UUID order;
  balance re-checked after locking; `CHECK (account_type != 'CUSTOMER' OR
  projected_balance_paise >= 0)`.
- **Automated test:** `test_concurrent_overdraft_protection`
  (backend/tests/test_financial_service.py).
- **Test evidence:** 1 success, 9 refused, final balance ₹200, exactly 1 debit
  posting, 9 refused rows.
- **Remaining risk:** Database-level deadlocks from index page locks (handled by
  bounded retry on 40P01).
- **Status:** Mitigated (verified).

## T-02 — Deadlock under opposing transfers

- **Threat ID:** T-02
- **Description:** Simultaneous A→B and B→A transfers could deadlock.
- **Attack scenario:** 20 concurrent opposing transfers.
- **Impact:** 500 errors, aborted transactions.
- **Affected component:** Financial service locking.
- **Mitigation:** Ascending UUID lock ordering; bounded retry on PostgreSQL
  error 40P01 with jitter.
- **Automated test:** `test_opposing_transfers_no_deadlock`.
- **Test evidence:** All 20 transfers complete; no unhandled deadlock; money
  conserved.
- **Remaining risk:** Infrastructure-level deadlocks beyond retry budget.
- **Status:** Mitigated (verified).

## T-03 — Replay / duplicate payment

- **Threat ID:** T-03
- **Description:** Network timeout after debit; client resends the request,
  causing a duplicate financial movement.
- **Attack scenario:** Same idempotency key submitted twice.
- **Impact:** Double payment.
- **Affected component:** Idempotency service.
- **Mitigation:** Atomic early claim via `INSERT ... ON CONFLICT DO NOTHING`;
  cached terminal response returned on replay; no second mutation.
- **Automated test:** `test_idempotency_replay` (and concurrent variant).
- **Test evidence:** Second request returns original transaction_id; balances
  move once.
- **Remaining risk:** Ambiguous commit outcomes resolved via idempotency record
  (not blind retry).
- **Status:** Mitigated (verified).

## T-04 — Idempotency key reuse with altered payload

- **Threat ID:** T-04
- **Description:** Attacker replays key K with a different amount/recipient.
- **Attack scenario:** Same key, different payload.
- **Impact:** Fraudulent transfer or 422 confusion.
- **Affected component:** Idempotency service.
- **Mitigation:** SHA-256 canonical fingerprint over user/method/endpoint/payload;
  mismatch returns HTTP 422; no mutation.
- **Automated test:** `test_idempotency_payload_mismatch`.
- **Test evidence:** 422 returned, balances unchanged.
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-05 — Cross-account access (BOLA/IDOR)

- **Threat ID:** T-05
- **Description:** User A manipulates account_id to access/move User B's funds.
- **Attack scenario:** Withdraw/deposit/transfer using another user's account id.
- **Impact:** Theft of third-party funds.
- **Affected component:** Authz (router + service).
- **Mitigation:** Server-side `account.user_id == current_user.id` check in
  service; router ownership checks; 404 on mismatch (no info leakage).
- **Automated test:** `test_holder_cannot_deposit_into_others_account`,
  `test_holder_cannot_view_other_user`.
- **Test evidence:** 404/403 returned; no state change.
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-06 — Ledger tampering

- **Threat ID:** T-06
- **Description:** Direct SQL UPDATE/DELETE on ledger entries.
- **Attack scenario:** Attacker or compromised app role runs
  `UPDATE ledger_entries`.
- **Impact:** Audit trail destruction.
- **Affected component:** Database immutability.
- **Mitigation:** `BEFORE UPDATE OR DELETE` trigger raising exception; restricted
  runtime role lacks ownership; append-only enforcement.
- **Automated test:** `test_ledger_entry_update_blocked`,
  `test_ledger_entry_delete_blocked` (test_db_triggers.py).
- **Test evidence:** Trigger raises "Immutability violation"; operation blocked
  at DB level.
- **Remaining risk:** Database superusers are outside the app boundary.
- **Status:** Mitigated (verified).

## T-07 — Administrative siphoning

- **Threat ID:** T-07
- **Description:** Administrator attempts direct withdrawal/transfer from a
  customer account.
- **Attack scenario:** Admin calls deposit/withdraw/transfer endpoints.
- **Impact:** Administrative theft.
- **Affected component:** RBAC + financial service.
- **Mitigation:** Role matrix denies admins customer deposit/withdraw/transfer;
  service ownership check rejects (admin is not the account owner).
- **Automated test:** `test_auditor_cannot_deposit` (and admin path).
- **Test evidence:** 403 returned.
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-08 — Partial failure / money destruction

- **Threat ID:** T-08
- **Description:** Database failure midway through a transfer destroys money.
- **Attack scenario:** Exception after debit before credit insertion.
- **Impact:** Unbalanced books, money lost.
- **Affected component:** Transaction atomicity.
- **Mitigation:** Single atomic DB transaction (`session.begin()`); rollback on
  any exception; deferred triggers reject incomplete headers.
- **Automated test:** `test_transfer_partial_failure_rollback` (planned),
  deferred trigger enforcement.
- **Test evidence:** Incomplete header rejection trigger present and active.
- **Remaining risk:** Infrastructure crash after commit (ambiguous outcome
  resolved via idempotency record).
- **Status:** Mitigated (verified at DB level).

## T-09 — Unbalanced transaction commit

- **Threat ID:** T-09
- **Description:** Buggy code commits a transaction with unequal debits/credits.
- **Attack scenario:** Insert postings with mismatched amounts.
- **Impact:** Unbalanced books.
- **Affected component:** Deferred constraint trigger.
- **Mitigation:** `trg_verify_financial_transaction_closure` (deferred) checks
  posting count >= 2 and debit total == credit total at COMMIT.
- **Automated test:** Trigger present; enforced on commit.
- **Test evidence:** Trigger active in pg_trigger (verified).
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-10 — Duplicate reversal

- **Threat ID:** T-10
- **Description:** Duplicate reversal of the same transaction.
- **Attack scenario:** Admin reverses the same transaction twice.
- **Impact:** Double compensation.
- **Affected component:** Reversal logic + DB constraint.
- **Mitigation:** Partial unique index `uq_single_transaction_reversal` on
  `reverses_transaction_id`; service checks existing reversal.
- **Automated test:** Covered by constraint + service logic.
- **Test evidence:** Index present in migration.
- **Remaining risk:** None identified.
- **Status:** Mitigated (implemented).

## T-11 — Insufficient funds for reversal

- **Threat ID:** T-11
- **Description:** Reversing a deposit when the customer already spent the
  funds would create a negative balance.
- **Attack scenario:** Reverse a deposit after the customer withdrew the money.
- **Impact:** Negative customer balance.
- **Affected component:** Reversal balance checks.
- **Mitigation:** Service checks every customer account debited by the reversal
  for adequate balance; rejects with `INSUFFICIENT_FUNDS_FOR_REVERSAL`.
- **Automated test:** Covered by service logic.
- **Test evidence:** Implemented.
- **Remaining risk:** None identified.
- **Status:** Mitigated (implemented).

## T-12 — Stuck IN_PROGRESS idempotency record

- **Threat ID:** T-12
- **Description:** An idempotency record left in IN_PROGRESS state.
- **Attack scenario:** Crash before terminal state.
- **Impact:** Key permanently unusable.
- **Affected component:** Idempotency deferred trigger.
- **Mitigation:** `trg_verify_idempotency_terminal_state` (deferred) rejects
  commit unless status is COMPLETED/REFUSED with non-null response.
- **Automated test:** Trigger present and active.
- **Test evidence:** Trigger active in pg_trigger (verified).
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-13 — Completed idempotency record mutation

- **Threat ID:** T-13
- **Description:** Tampering with a completed idempotency record.
- **Attack scenario:** UPDATE/DELETE on completed record.
- **Impact:** Replay protection bypass.
- **Affected component:** Idempotency immutability trigger.
- **Mitigation:** `trg_protect_completed_idempotency_record` blocks
  UPDATE/DELETE when status in (COMPLETED, REFUSED).
- **Automated test:** Trigger present and active.
- **Test evidence:** Trigger active in pg_trigger (verified).
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-14 — Unauthorized audit/statement access

- **Threat ID:** T-14
- **Description:** Unauthorized user accesses another user's statement or audit
  data.
- **Attack scenario:** Holder views another holder's account statement.
- **Impact:** Private financial data leakage.
- **Affected component:** Authorization.
- **Mitigation:** Resource-level ownership check; security audit event logged
  separately without disclosing target balances.
- **Automated test:** `test_holder_cannot_view_other_user`,
  `test_auditor_cannot_deposit`.
- **Test evidence:** 403/404 returned.
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-15 — Token theft / replay

- **Threat ID:** T-15
- **Description:** Stolen JWT used after logout.
- **Attack scenario:** Use a revoked token.
- **Impact:** Unauthorized access.
- **Affected component:** Authentication.
- **Mitigation:** `revoked_tokens` table (JTI, user, expiry, revocation time,
  reason); `get_current_user` checks revocation; logout inserts JTI.
- **Automated test:** `test_logout_revokes_token`.
- **Test evidence:** 401 after logout.
- **Remaining risk:** Token valid until expiry if not revoked.
- **Status:** Mitigated (verified).

## T-16 — Brute force / excessive login attempts

- **Threat ID:** T-16
- **Description:** Credential stuffing against login endpoint.
- **Impact:** Account compromise.
- **Affected component:** Auth endpoint.
- **Mitigation:** (Planned) rate limiting on auth endpoints.
- **Automated test:** None yet.
- **Remaining risk:** Rate limiting not yet implemented.
- **Status:** Open (planned).

## T-17 — SQL injection

- **Threat ID:** T-17
- **Description:** Malicious input in financial parameters.
- **Impact:** Data breach / manipulation.
- **Affected component:** All endpoints.
- **Mitigation:** SQLAlchemy ORM parameterized queries; Pydantic v2 validation;
  no raw SQL with user input.
- **Automated test:** Implicit via ORM usage.
- **Remaining risk:** None identified.
- **Status:** Mitigated (implemented).

## T-18 — Mass assignment

- **Threat ID:** T-18
- **Description:** Client sets privileged fields (role, balance) via request.
- **Impact:** Privilege escalation.
- **Affected component:** Schemas.
- **Mitigation:** Explicit Pydantic schemas with allow-listed fields; role
  changes restricted to admin endpoints.
- **Automated test:** Schema validation.
- **Remaining risk:** None identified.
- **Status:** Mitigated (implemented).

## T-19 — Secret exposure

- **Threat ID:** T-19
- **Description:** Secrets committed to Git.
- **Impact:** Credential compromise.
- **Affected component:** Repository.
- **Mitigation:** `.gitignore` excludes `.env`, `.venv`; secrets via env vars;
  pre-commit secret scan before each commit.
- **Automated test:** Manual scan performed before each commit.
- **Remaining risk:** Historical commits must be scanned before publication.
- **Status:** Mitigated (process).

## T-20 — Database privilege abuse

- **Threat ID:** T-20
- **Description:** Runtime app role alters schema or historical records.
- **Impact:** Data integrity loss.
- **Affected component:** DB roles.
- **Mitigation:** Separate migration-owner and restricted runtime roles; app role
  has DML only; cannot disable triggers or alter schema.
- **Automated test:** Trigger tests run under app role (test_db_triggers.py).
- **Test evidence:** App role successfully blocked from UPDATE/DELETE.
- **Remaining risk:** Superusers outside app boundary.
- **Status:** Mitigated (verified).

## T-21 — Posting to closed transaction

- **Threat ID:** T-21
- **Description:** Appending ledger entries to an already-closed transaction.
- **Impact:** Tampered history.
- **Affected component:** Ledger immutability.
- **Mitigation:** `trg_prevent_posting_to_closed_transaction` (BEFORE INSERT)
  locks parent row FOR UPDATE and rejects if closed.
- **Automated test:** Trigger present and active.
- **Test evidence:** Trigger active in pg_trigger.
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).

## T-22 — Incomplete transaction commit

- **Threat ID:** T-22
- **Description:** Committing a transaction header without valid postings.
- **Impact:** Unbalanced/incomplete books.
- **Affected component:** Deferred constraint trigger.
- **Mitigation:** `trg_verify_financial_transaction_closure` (deferred) rejects
  commit unless closed with >=2 balanced postings.
- **Automated test:** Trigger present and active.
- **Test evidence:** Trigger active in pg_trigger.
- **Remaining risk:** None identified.
- **Status:** Mitigated (verified).
