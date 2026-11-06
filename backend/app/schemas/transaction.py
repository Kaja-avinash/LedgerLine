"""Pydantic schemas for financial transactions."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class DepositRequest(BaseModel):
    account_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    currency: str = "INR"
    description: str = "Simulated deposit"
    metadata: dict[str, Any] = {}


class WithdrawRequest(BaseModel):
    account_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    currency: str = "INR"
    description: str = "Simulated withdrawal"
    metadata: dict[str, Any] = {}


class TransferRequest(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    currency: str = "INR"
    description: str = "Internal transfer"
    metadata: dict[str, Any] = {}


class ReverseRequest(BaseModel):
    reason: str = Field(min_length=1)


class TransactionResponse(BaseModel):
    transaction_id: str | None = None
    transaction_type: str | None = None
    status: str | None = None
    amount_paise: int | None = None
    account_id: str | None = None
    new_balance_paise: int | None = None
    from_account_id: str | None = None
    to_account_id: str | None = None
    source_new_balance_paise: int | None = None
    destination_new_balance_paise: int | None = None
    reverses_transaction_id: str | None = None
    error_code: str | None = None
    message: str | None = None
    observed_balance_paise: int | None = None

    model_config = {"extra": "allow"}
