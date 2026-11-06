"""Pydantic schemas for accounts."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AccountCreateRequest(BaseModel):
    user_id: uuid.UUID
    account_type: str = Field(pattern="^(CUSTOMER|SYSTEM_CLEARING_DEPOSIT|SYSTEM_CLEARING_WITHDRAWAL)$")
    currency: str = "INR"


class AccountResponse(BaseModel):
    id: uuid.UUID
    account_number: str
    user_id: uuid.UUID | None
    account_type: str
    currency: str
    status: str
    projected_balance_paise: int
    last_activity_sequence: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StatementItem(BaseModel):
    kind: str
    entry_type: str
    amount_paise: int
    running_balance_paise: int
    account_activity_sequence: int
    created_at: datetime
    transaction_id: uuid.UUID | None = None


class AccountStatementResponse(BaseModel):
    account_id: uuid.UUID
    account_number: str
    projected_balance_paise: int
    items: list[StatementItem]
