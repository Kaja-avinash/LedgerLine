"""Read-only reconciliation engine."""

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.financial_transaction import FinancialTransaction
from app.models.ledger_entry import LedgerEntry


class ReconciliationService:
    def __init__(self, db: Session):
        self.db = db

    def run(self) -> dict:
        issues: list[str] = []

        # 1. Per-account ledger vs projected balance.
        accounts = self.db.query(Account).all()
        for acc in accounts:
            postings = (
                self.db.query(LedgerEntry)
                .filter(LedgerEntry.account_id == acc.id)
                .all()
            )
            debits = sum(p.amount_paise for p in postings if p.entry_type == "DEBIT")
            credits = sum(p.amount_paise for p in postings if p.entry_type == "CREDIT")
            if acc.account_type == "CUSTOMER":
                ledger_balance = credits - debits
            elif acc.account_type == "SYSTEM_CLEARING_DEPOSIT":
                ledger_balance = debits - credits
            else:  # SYSTEM_CLEARING_WITHDRAWAL
                ledger_balance = credits - debits
            if ledger_balance != acc.projected_balance_paise:
                issues.append(
                    f"Account {acc.id} ({acc.account_type}): ledger={ledger_balance} "
                    f"!= projected={acc.projected_balance_paise}"
                )
            if acc.account_type == "CUSTOMER" and acc.projected_balance_paise < 0:
                issues.append(f"Account {acc.id}: negative customer balance")

        # 2. Every transaction balanced.
        txns = self.db.query(FinancialTransaction).filter(FinancialTransaction.is_closed.is_(True)).all()
        for t in txns:
            postings = (
                self.db.query(LedgerEntry)
                .filter(LedgerEntry.transaction_id == t.id)
                .all()
            )
            if len(postings) < 2:
                issues.append(f"Transaction {t.id}: fewer than 2 postings")
                continue
            debits = sum(p.amount_paise for p in postings if p.entry_type == "DEBIT")
            credits = sum(p.amount_paise for p in postings if p.entry_type == "CREDIT")
            if debits != credits:
                issues.append(
                    f"Transaction {t.id}: unbalanced (debits={debits}, credits={credits})"
                )

        # 3. Internal transfers conserve customer money (sum of postings = 0).
        transfer_txns = [t for t in txns if t.transaction_type == "TRANSFER"]
        for t in transfer_txns:
            postings = (
                self.db.query(LedgerEntry)
                .filter(LedgerEntry.transaction_id == t.id)
                .all()
            )
            signed = sum(
                p.amount_paise if p.entry_type == "CREDIT" else -p.amount_paise for p in postings
            )
            if signed != 0:
                issues.append(f"Transfer {t.id}: does not conserve (signed sum={signed})")

        return {
            "status": "ok" if not issues else "issues_found",
            "issue_count": len(issues),
            "issues": issues,
            "accounts_checked": len(accounts),
            "transactions_checked": len(txns),
        }
