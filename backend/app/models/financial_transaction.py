"""Financial transaction header (controlled closure)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    initiator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reference_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    transaction_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="'{}'::jsonb"
    )
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reverses_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_transactions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'REVERSAL')",
            name="chk_transaction_type",
        ),
        # Partial unique index: at most one full reversal per original.
        Index(
            "uq_single_transaction_reversal",
            "reverses_transaction_id",
            unique=True,
            postgresql_where="reverses_transaction_id IS NOT NULL",
        ),
    )

    initiator: Mapped["User"] = relationship()
    postings: Mapped[list["LedgerEntry"]] = relationship(back_populates="transaction")
    reversed_original: Mapped["FinancialTransaction | None"] = relationship(
        remote_side=[id], foreign_keys=[reverses_transaction_id]
    )