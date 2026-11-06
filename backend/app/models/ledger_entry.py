"""Ledger entry (append-only double-entry posting)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_activity_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    running_balance_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("entry_type IN ('DEBIT', 'CREDIT')", name="chk_entry_type"),
        CheckConstraint("amount_paise > 0", name="chk_amount_positive"),
        UniqueConstraint(
            "account_id", "account_activity_sequence", name="uq_account_ledger_sequence"
        ),
    )

    transaction: Mapped["FinancialTransaction"] = relationship(back_populates="postings")
    account: Mapped["Account"] = relationship(back_populates="ledger_entries")