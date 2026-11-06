"""Account model (customer & system clearing accounts)."""

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


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", server_default="ACTIVE")
    projected_balance_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    last_activity_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("currency = 'INR'", name="chk_currency_inr"),
        CheckConstraint(
            "account_type != 'CUSTOMER' OR projected_balance_paise >= 0",
            name="chk_customer_balance_non_negative",
        ),
        CheckConstraint(
            "account_type IN ('CUSTOMER', 'SYSTEM_CLEARING_DEPOSIT', 'SYSTEM_CLEARING_WITHDRAWAL')",
            name="chk_account_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'FROZEN', 'CLOSED')",
            name="chk_account_status",
        ),
    )

    user: Mapped["User | None"] = relationship(back_populates="accounts")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="account")
    refused_operations: Mapped[list["RefusedOperation"]] = relationship(back_populates="account")