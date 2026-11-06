"""Core financial transaction service (synchronous).

Implements idempotency claiming, deterministic locking, double-entry postings,
balance projections, account activity sequencing, and reversals.
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.financial_transaction import FinancialTransaction
from app.models.idempotency import IdempotencyRecord
from app.models.ledger_entry import LedgerEntry
from app.models.refused_operation import RefusedOperation
from app.models.user import User


class FinancialError(Exception):
    """Base domain error for financial operations."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class InsufficientFundsError(FinancialError):
    def __init__(self, message: str = "Insufficient funds"):
        super().__init__("INSUFFICIENT_FUNDS", message, 400)


class AccountFrozenError(FinancialError):
    def __init__(self, message: str = "Account is frozen"):
        super().__init__("ACCOUNT_FROZEN", message, 400)


class InvalidAccountError(FinancialError):
    def __init__(self, message: str = "Invalid account"):
        super().__init__("INVALID_ACCOUNT", message, 400)


class SelfTransferError(FinancialError):
    def __init__(self, message: str = "Self-transfer is not allowed"):
        super().__init__("SELF_TRANSFER", message, 400)


class CurrencyMismatchError(FinancialError):
    def __init__(self, message: str = "Currency mismatch"):
        super().__init__("CURRENCY_MISMATCH", message, 400)


class IdempotencyConflictError(FinancialError):
    def __init__(self, message: str = "Idempotency key reused with different payload"):
        super().__init__("IDEMPOTENCY_PAYLOAD_MISMATCH", message, 422)


@dataclass
class FinancialResult:
    status_code: int
    body: dict[str, Any]
    transaction_id: uuid.UUID | None = None


class FinancialService:
    MAX_RETRIES = 3

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # Public operations
    # ------------------------------------------------------------------ #
    def deposit(
        self,
        *,
        initiator: User,
        account_id: uuid.UUID,
        amount_paise: int,
        currency: str = "INR",
        idempotency_key: str,
        request_path: str,
        request_method: str = "POST",
        request_payload: dict[str, Any],
        description: str = "Simulated deposit",
        metadata: dict[str, Any] | None = None,
    ) -> FinancialResult:
        request_hash = self._fingerprint(initiator.id, request_method, request_path, request_payload)
        return self._run(
            lambda: self._deposit_impl(
                initiator=initiator,
                account_id=account_id,
                amount_paise=amount_paise,
                currency=currency,
                idempotency_key=idempotency_key,
                request_path=request_path,
                request_method=request_method,
                request_hash=request_hash,
                description=description,
                metadata=metadata or {},
            )
        )

    def withdraw(
        self,
        *,
        initiator: User,
        account_id: uuid.UUID,
        amount_paise: int,
        currency: str = "INR",
        idempotency_key: str,
        request_path: str,
        request_method: str = "POST",
        request_payload: dict[str, Any],
        description: str = "Simulated withdrawal",
        metadata: dict[str, Any] | None = None,
    ) -> FinancialResult:
        request_hash = self._fingerprint(initiator.id, request_method, request_path, request_payload)
        return self._run(
            lambda: self._withdraw_impl(
                initiator=initiator,
                account_id=account_id,
                amount_paise=amount_paise,
                currency=currency,
                idempotency_key=idempotency_key,
                request_path=request_path,
                request_method=request_method,
                request_hash=request_hash,
                description=description,
                metadata=metadata or {},
            )
        )

    def transfer(
        self,
        *,
        initiator: User,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount_paise: int,
        currency: str = "INR",
        idempotency_key: str,
        request_path: str,
        request_method: str = "POST",
        request_payload: dict[str, Any],
        description: str = "Internal transfer",
        metadata: dict[str, Any] | None = None,
    ) -> FinancialResult:
        request_hash = self._fingerprint(initiator.id, request_method, request_path, request_payload)
        return self._run(
            lambda: self._transfer_impl(
                initiator=initiator,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount_paise=amount_paise,
                currency=currency,
                idempotency_key=idempotency_key,
                request_path=request_path,
                request_method=request_method,
                request_hash=request_hash,
                description=description,
                metadata=metadata or {},
            )
        )

    # ------------------------------------------------------------------ #
    # Retry wrapper (bounded, safe) for deadlock 40P01
    # ------------------------------------------------------------------ #
    def _run(self, fn: Callable[[], FinancialResult]) -> FinancialResult:
        last_exc: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Prevent indefinite hangs on row-lock contention.
                self.db.execute(text("SET LOCAL lock_timeout = '5s'"))
                result = fn()
                self.db.commit()
                return result
            except OperationalError as exc:
                self.db.rollback()
                last_exc = exc
                if attempt < self.MAX_RETRIES - 1 and self._is_deadlock(exc):
                    time.sleep(0.02 * (2 ** attempt))
                    continue
                raise
            except Exception:
                self.db.rollback()
                raise
        if last_exc is not None:
            raise last_exc
        raise FinancialError("UNEXPECTED", "Unexpected financial failure", 500)

    # ------------------------------------------------------------------ #
    # Idempotency
    # ------------------------------------------------------------------ #
    def _claim_key(
        self,
        *,
        user_id: uuid.UUID,
        key: str,
        request_path: str,
        request_method: str,
        request_hash: str,
    ) -> tuple[bool, IdempotencyRecord]:
        """Attempt to claim the key. Returns (claimed, record)."""
        result = self.db.execute(
            text(
                "INSERT INTO idempotency_records "
                "(user_id, key, request_path, request_method, request_hash, status) "
                "VALUES (:uid, :key, :path, :method, :hash, 'IN_PROGRESS') "
                "ON CONFLICT (user_id, key) DO NOTHING "
                "RETURNING user_id, key"
            ),
            {
                "uid": user_id,
                "key": key,
                "path": request_path,
                "method": request_method,
                "hash": request_hash,
            },
        )
        row = result.fetchone()
        if row is not None:
            rec = (
                self.db.query(IdempotencyRecord)
                .filter(
                    IdempotencyRecord.user_id == user_id,
                    IdempotencyRecord.key == key,
                )
                .first()
            )
            return True, rec
        # Key already exists (or was claimed by a concurrent txn).
        # Wait briefly for the competing transaction to resolve.
        for _ in range(100):
            rec = (
                self.db.query(IdempotencyRecord)
                .filter(
                    IdempotencyRecord.user_id == user_id,
                    IdempotencyRecord.key == key,
                )
                .first()
            )
            if rec is not None and rec.status in ("COMPLETED", "REFUSED"):
                return False, rec
            time.sleep(0.01)
        rec = (
            self.db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.key == key,
            )
            .first()
        )
        return False, rec

    def _verify_replay(
        self, record: IdempotencyRecord, request_hash: str
    ) -> FinancialResult | None:
        """If record is terminal and hash matches, return cached result. Else raise."""
        if record.request_hash != request_hash:
            raise IdempotencyConflictError()
        if record.status == "COMPLETED":
            body = record.response_body or {}
            return FinancialResult(
                status_code=record.response_status_code or 200,
                body=body,
                transaction_id=record.transaction_id,
            )
        if record.status == "REFUSED":
            body = record.response_body or {}
            # Re-raise the original refusal as a FinancialError if code present.
            code = body.get("error_code", "REFUSED")
            msg = body.get("message", "Request refused")
            sc = record.response_status_code or 400
            raise FinancialError(code, msg, sc)
        # IN_PROGRESS (shouldn't happen for committed record) -> treat as conflict
        raise FinancialError("IDEMPOTENCY_IN_PROGRESS", "Request is still processing", 409)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fingerprint(user_id, method, path, payload) -> str:
        canonical = json.dumps(
            {
                "user_id": str(user_id),
                "method": method,
                "path": path,
                "payload": payload,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _is_deadlock(exc: OperationalError) -> bool:
        msg = str(exc).lower()
        return "40p01" in msg or "deadlock" in msg

    def _get_system_account(self, account_type: str) -> Account:
        acc = (
            self.db.query(Account)
            .filter(Account.account_type == account_type)
            .first()
        )
        if acc is None:
            raise InvalidAccountError(f"System account {account_type} not found")
        return acc

    def _lock_accounts(self, account_ids: list[uuid.UUID]) -> dict[uuid.UUID, Account]:
        locked: dict[uuid.UUID, Account] = {}
        for aid in sorted(set(account_ids)):
            acc = (
                self.db.execute(
                    select(Account).where(Account.id == aid).with_for_update()
                )
                .scalar_one_or_none()
            )
            if acc is None:
                raise InvalidAccountError(f"Account {aid} not found")
            locked[aid] = acc
        return locked

    def _next_seq(self, account: Account) -> int:
        account.last_activity_sequence = account.last_activity_sequence + 1
        return account.last_activity_sequence

    def _validate_amount(self, amount_paise: int) -> None:
        if not isinstance(amount_paise, int) or isinstance(amount_paise, bool):
            raise FinancialError("INVALID_AMOUNT", "Amount must be an integer (paise)", 400)
        if amount_paise <= 0:
            raise FinancialError("INVALID_AMOUNT", "Amount must be positive", 400)

    def _validate_currency(self, account: Account, currency: str) -> None:
        if account.currency != currency:
            raise CurrencyMismatchError()
        if currency != "INR":
            raise FinancialError("UNSUPPORTED_CURRENCY", "Only INR is supported", 400)

    def _validate_active(self, account: Account) -> None:
        if account.status != "ACTIVE":
            raise AccountFrozenError(f"Account is {account.status}")

    # ------------------------------------------------------------------ #
    # Deposit
    # ------------------------------------------------------------------ #
    def _deposit_impl(
        self,
        *,
        initiator: User,
        account_id: uuid.UUID,
        amount_paise: int,
        currency: str,
        idempotency_key: str,
        request_path: str,
        request_method: str,
        request_hash: str,
        description: str,
        metadata: dict[str, Any],
    ) -> FinancialResult:
        self._validate_amount(amount_paise)
        claimed, record = self._claim_key(
            user_id=initiator.id,
            key=idempotency_key,
            request_path=request_path,
            request_method=request_method,
            request_hash=request_hash,
        )
        if not claimed:
            return self._verify_replay(record, request_hash)

        # Lock accounts: customer + deposit clearing
        clearing = self._get_system_account("SYSTEM_CLEARING_DEPOSIT")
        locked = self._lock_accounts([account_id, clearing.id])
        customer = locked[account_id]
        clearing = locked[clearing.id]

        self._validate_currency(customer, currency)
        self._validate_currency(clearing, currency)
        self._validate_active(customer)
        self._validate_active(clearing)

        # Ownership: account must belong to initiator OR initiator is an ADMINISTRATOR.
        # Admins may fund any customer account for operational/testing purposes.
        if customer.user_id != initiator.id and initiator.role != "ADMINISTRATOR":
            raise FinancialError("FORBIDDEN", "Cannot deposit into another user's account", 403)

        # Update balances
        customer.projected_balance_paise += amount_paise
        clearing.projected_balance_paise += amount_paise  # debit-normal: debits increase

        # Activity sequences
        cust_seq = self._next_seq(customer)
        clr_seq = self._next_seq(clearing)

        # Transaction header
        txn = FinancialTransaction(
            transaction_type="DEPOSIT",
            initiator_user_id=initiator.id,
            reference_id=f"DEP-{uuid.uuid4()}",
            description=description,
            transaction_metadata=metadata,
            is_closed=False,
        )
        self.db.add(txn)
        self.db.flush()

        # Postings
        self.db.add(
            LedgerEntry(
                transaction_id=txn.id,
                account_id=clearing.id,
                entry_type="DEBIT",
                amount_paise=amount_paise,
                account_activity_sequence=clr_seq,
                running_balance_paise=clearing.projected_balance_paise,
            )
        )
        self.db.add(
            LedgerEntry(
                transaction_id=txn.id,
                account_id=customer.id,
                entry_type="CREDIT",
                amount_paise=amount_paise,
                account_activity_sequence=cust_seq,
                running_balance_paise=customer.projected_balance_paise,
            )
        )

        self.db.flush()

        # Close header
        txn.is_closed = True
        txn.posted_at = datetime.now(timezone.utc)

        # Idempotency result
        body = {
            "transaction_id": str(txn.id),
            "transaction_type": "DEPOSIT",
            "amount_paise": amount_paise,
            "account_id": str(customer.id),
            "new_balance_paise": customer.projected_balance_paise,
            "status": "COMPLETED",
        }
        record.status = "COMPLETED"
        record.response_status_code = 200
        record.response_body = body
        record.transaction_id = txn.id

        return FinancialResult(status_code=200, body=body, transaction_id=txn.id)

    # ------------------------------------------------------------------ #
    # Withdrawal
    # ------------------------------------------------------------------ #
    def _withdraw_impl(
        self,
        *,
        initiator: User,
        account_id: uuid.UUID,
        amount_paise: int,
        currency: str,
        idempotency_key: str,
        request_path: str,
        request_method: str,
        request_hash: str,
        description: str,
        metadata: dict[str, Any],
    ) -> FinancialResult:
        self._validate_amount(amount_paise)
        claimed, record = self._claim_key(
            user_id=initiator.id,
            key=idempotency_key,
            request_path=request_path,
            request_method=request_method,
            request_hash=request_hash,
        )
        if not claimed:
            return self._verify_replay(record, request_hash)

        clearing = self._get_system_account("SYSTEM_CLEARING_WITHDRAWAL")
        locked = self._lock_accounts([account_id, clearing.id])
        customer = locked[account_id]
        clearing = locked[clearing.id]

        self._validate_currency(customer, currency)
        self._validate_currency(clearing, currency)
        self._validate_active(customer)
        self._validate_active(clearing)

        # Ownership: account must belong to initiator OR initiator is an ADMINISTRATOR.
        if customer.user_id != initiator.id and initiator.role != "ADMINISTRATOR":
            raise FinancialError("FORBIDDEN", "Cannot withdraw from another user's account", 403)

        # Business refusal: insufficient funds
        if customer.projected_balance_paise < amount_paise:
            observed = customer.projected_balance_paise
            seq = self._next_seq(customer)
            self.db.add(
                RefusedOperation(
                    user_id=initiator.id,
                    account_id=customer.id,
                    observed_balance_paise=observed,
                    account_activity_sequence=seq,
                    operation_type="WITHDRAWAL",
                    attempted_amount_paise=amount_paise,
                    reason_code="INSUFFICIENT_FUNDS",
                    reason_message="Insufficient funds for withdrawal",
                    idempotency_key=idempotency_key,
                    request_metadata=metadata,
                )
            )
            body = {
                "error_code": "INSUFFICIENT_FUNDS",
                "message": "Insufficient funds for withdrawal",
                "observed_balance_paise": observed,
                "status": "REFUSED",
            }
            record.status = "REFUSED"
            record.response_status_code = 400
            record.response_body = body
            record.transaction_id = None
            self.db.commit()
            raise InsufficientFundsError("Insufficient funds for withdrawal")

        # Update balances
        customer.projected_balance_paise -= amount_paise
        clearing.projected_balance_paise += amount_paise  # credit-normal: credits increase

        cust_seq = self._next_seq(customer)
        clr_seq = self._next_seq(clearing)

        txn = FinancialTransaction(
            transaction_type="WITHDRAWAL",
            initiator_user_id=initiator.id,
            reference_id=f"WDR-{uuid.uuid4()}",
            description=description,
            transaction_metadata=metadata,
            is_closed=False,
        )
        self.db.add(txn)
        self.db.flush()

        self.db.add(
            LedgerEntry(
                transaction_id=txn.id,
                account_id=customer.id,
                entry_type="DEBIT",
                amount_paise=amount_paise,
                account_activity_sequence=cust_seq,
                running_balance_paise=customer.projected_balance_paise,
            )
        )
        self.db.add(
            LedgerEntry(
                transaction_id=txn.id,
                account_id=clearing.id,
                entry_type="CREDIT",
                amount_paise=amount_paise,
                account_activity_sequence=clr_seq,
                running_balance_paise=clearing.projected_balance_paise,
            )
        )

        self.db.flush()

        txn.is_closed = True
        txn.posted_at = datetime.now(timezone.utc)

        body = {
            "transaction_id": str(txn.id),
            "transaction_type": "WITHDRAWAL",
            "amount_paise": amount_paise,
            "account_id": str(customer.id),
            "new_balance_paise": customer.projected_balance_paise,
            "status": "COMPLETED",
        }
        record.status = "COMPLETED"
        record.response_status_code = 200
        record.response_body = body
        record.transaction_id = txn.id

        return FinancialResult(status_code=200, body=body, transaction_id=txn.id)

    # ------------------------------------------------------------------ #
    # Transfer
    # ------------------------------------------------------------------ #
    def _transfer_impl(
        self,
        *,
        initiator: User,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount_paise: int,
        currency: str,
        idempotency_key: str,
        request_path: str,
        request_method: str,
        request_hash: str,
        description: str,
        metadata: dict[str, Any],
    ) -> FinancialResult:
        self._validate_amount(amount_paise)
        if from_account_id == to_account_id:
            raise SelfTransferError()

        claimed, record = self._claim_key(
            user_id=initiator.id,
            key=idempotency_key,
            request_path=request_path,
            request_method=request_method,
            request_hash=request_hash,
        )
        if not claimed:
            return self._verify_replay(record, request_hash)

        locked = self._lock_accounts([from_account_id, to_account_id])
        source = locked[from_account_id]
        dest = locked[to_account_id]

        self._validate_currency(source, currency)
        self._validate_currency(dest, currency)
        self._validate_active(source)
        self._validate_active(dest)

        # Ownership: source account must belong to initiator OR initiator is an ADMINISTRATOR.
        if source.user_id != initiator.id and initiator.role != "ADMINISTRATOR":
            raise FinancialError("FORBIDDEN", "Cannot transfer from another user's account", 403)
        if dest.user_id is None:
            raise InvalidAccountError("Destination account has no owner")

        # Business refusal: insufficient funds
        if source.projected_balance_paise < amount_paise:
            observed = source.projected_balance_paise
            seq = self._next_seq(source)
            self.db.add(
                RefusedOperation(
                    user_id=initiator.id,
                    account_id=source.id,
                    observed_balance_paise=observed,
                    account_activity_sequence=seq,
                    operation_type="TRANSFER",
                    attempted_amount_paise=amount_paise,
                    reason_code="INSUFFICIENT_FUNDS",
                    reason_message="Insufficient funds for transfer",
                    idempotency_key=idempotency_key,
                    request_metadata=metadata,
                )
            )
            body = {
                "error_code": "INSUFFICIENT_FUNDS",
                "message": "Insufficient funds for transfer",
                "observed_balance_paise": observed,
                "status": "REFUSED",
            }
            record.status = "REFUSED"
            record.response_status_code = 400
            record.response_body = body
            record.transaction_id = None
            self.db.commit()
            raise InsufficientFundsError("Insufficient funds for transfer")

        # Update balances
        source.projected_balance_paise -= amount_paise
        dest.projected_balance_paise += amount_paise

        src_seq = self._next_seq(source)
        dst_seq = self._next_seq(dest)

        txn = FinancialTransaction(
            transaction_type="TRANSFER",
            initiator_user_id=initiator.id,
            reference_id=f"TRF-{uuid.uuid4()}",
            description=description,
            transaction_metadata=metadata,
            is_closed=False,
        )
        self.db.add(txn)
        self.db.flush()

        self.db.add(
            LedgerEntry(
                transaction_id=txn.id,
                account_id=source.id,
                entry_type="DEBIT",
                amount_paise=amount_paise,
                account_activity_sequence=src_seq,
                running_balance_paise=source.projected_balance_paise,
            )
        )
        self.db.add(
            LedgerEntry(
                transaction_id=txn.id,
                account_id=dest.id,
                entry_type="CREDIT",
                amount_paise=amount_paise,
                account_activity_sequence=dst_seq,
                running_balance_paise=dest.projected_balance_paise,
            )
        )

        self.db.flush()

        txn.is_closed = True
        txn.posted_at = datetime.now(timezone.utc)

        body = {
            "transaction_id": str(txn.id),
            "transaction_type": "TRANSFER",
            "amount_paise": amount_paise,
            "from_account_id": str(source.id),
            "to_account_id": str(dest.id),
            "source_new_balance_paise": source.projected_balance_paise,
            "destination_new_balance_paise": dest.projected_balance_paise,
            "status": "COMPLETED",
        }
        record.status = "COMPLETED"
        record.response_status_code = 200
        record.response_body = body
        record.transaction_id = txn.id

        return FinancialResult(status_code=200, body=body, transaction_id=txn.id)

    # ------------------------------------------------------------------ #
    # Reversal (full only)
    # ------------------------------------------------------------------ #
    def reverse(
        self,
        *,
        initiator: "User",
        original_transaction_id: uuid.UUID,
        reason: str,
        idempotency_key: str,
        request_path: str,
        request_method: str = "POST",
        request_payload: dict[str, Any],
    ) -> FinancialResult:
        request_hash = self._fingerprint(initiator.id, request_method, request_path, request_payload)
        return self._run(
            lambda: self._reverse_impl(
                initiator=initiator,
                original_transaction_id=original_transaction_id,
                reason=reason,
                idempotency_key=idempotency_key,
                request_path=request_path,
                request_method=request_method,
                request_hash=request_hash,
            )
        )

    def _reverse_impl(
        self,
        *,
        initiator: "User",
        original_transaction_id: uuid.UUID,
        reason: str,
        idempotency_key: str,
        request_path: str,
        request_method: str,
        request_hash: str,
    ) -> FinancialResult:
        if not reason or not reason.strip():
            raise FinancialError("REASON_REQUIRED", "Reversal requires a reason narrative", 400)

        claimed, record = self._claim_key(
            user_id=initiator.id,
            key=idempotency_key,
            request_path=request_path,
            request_method=request_method,
            request_hash=request_hash,
        )
        if not claimed:
            return self._verify_replay(record, request_hash)

        original = (
            self.db.query(FinancialTransaction)
            .filter(FinancialTransaction.id == original_transaction_id)
            .first()
        )
        if original is None:
            raise FinancialError("ORIGINAL_NOT_FOUND", "Original transaction not found", 404)
        if not original.is_closed:
            raise FinancialError("ORIGINAL_NOT_COMPLETED", "Original transaction is not completed", 400)
        if original.reverses_transaction_id is not None:
            raise FinancialError("CANNOT_REVERSE_REVERSAL", "A reversal cannot be reversed", 400)

        existing_reversal = (
            self.db.query(FinancialTransaction)
            .filter(FinancialTransaction.reverses_transaction_id == original.id)
            .first()
        )
        if existing_reversal is not None:
            raise FinancialError("ALREADY_REVERSED", "Transaction already has a reversal", 400)

        postings = (
            self.db.query(LedgerEntry)
            .filter(LedgerEntry.transaction_id == original.id)
            .all()
        )
        if not postings:
            raise FinancialError("INVALID_ORIGINAL", "Original has no postings", 400)

        account_ids = [p.account_id for p in postings]
        locked = self._lock_accounts(account_ids)

        for p in postings:
            if p.entry_type == "CREDIT":
                acc = locked[p.account_id]
                if acc.account_type == "CUSTOMER" and acc.projected_balance_paise < p.amount_paise:
                    observed = acc.projected_balance_paise
                    seq = self._next_seq(acc)
                    self.db.add(
                        RefusedOperation(
                            user_id=initiator.id,
                            account_id=acc.id,
                            observed_balance_paise=observed,
                            account_activity_sequence=seq,
                            operation_type="REVERSAL",
                            attempted_amount_paise=p.amount_paise,
                            reason_code="INSUFFICIENT_FUNDS_FOR_REVERSAL",
                            reason_message="Insufficient funds for reversal",
                            idempotency_key=idempotency_key,
                            request_metadata={"original_transaction_id": str(original.id)},
                        )
                    )
                    body = {
                        "error_code": "INSUFFICIENT_FUNDS_FOR_REVERSAL",
                        "message": "Insufficient funds for reversal",
                        "status": "REFUSED",
                    }
                    record.status = "REFUSED"
                    record.response_status_code = 400
                    record.response_body = body
                    record.transaction_id = None
                    self.db.commit()
                    raise InsufficientFundsError("Insufficient funds for reversal")

        for p in postings:
            acc = locked[p.account_id]
            if p.entry_type == "DEBIT":
                acc.projected_balance_paise += p.amount_paise
            else:
                acc.projected_balance_paise -= p.amount_paise
            self._validate_active(acc)

        seqs = {aid: self._next_seq(locked[aid]) for aid in set(account_ids)}

        txn = FinancialTransaction(
            transaction_type="REVERSAL",
            initiator_user_id=initiator.id,
            reference_id=f"REV-{uuid.uuid4()}",
            description=f"Reversal of {original.reference_id}: {reason}",
            transaction_metadata={"original_transaction_id": str(original.id), "reason": reason},
            reverses_transaction_id=original.id,
            is_closed=False,
        )
        self.db.add(txn)
        self.db.flush()

        for p in postings:
            inv_type = "CREDIT" if p.entry_type == "DEBIT" else "DEBIT"
            self.db.add(
                LedgerEntry(
                    transaction_id=txn.id,
                    account_id=p.account_id,
                    entry_type=inv_type,
                    amount_paise=p.amount_paise,
                    account_activity_sequence=seqs[p.account_id],
                    running_balance_paise=locked[p.account_id].projected_balance_paise,
                )
            )

        self.db.flush()
        txn.is_closed = True
        txn.posted_at = datetime.now(timezone.utc)

        body = {
            "transaction_id": str(txn.id),
            "transaction_type": "REVERSAL",
            "reverses_transaction_id": str(original.id),
            "status": "COMPLETED",
        }
        record.status = "COMPLETED"
        record.response_status_code = 200
        record.response_body = body
        record.transaction_id = txn.id

        return FinancialResult(status_code=200, body=body, transaction_id=txn.id)
