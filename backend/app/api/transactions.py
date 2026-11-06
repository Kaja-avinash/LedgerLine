"""Financial transaction routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.security import decode_access_token
from app.models.account import Account
from app.models.user import User
from app.schemas.transaction import (
    DepositRequest,
    ReverseRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)
from app.services.financial import FinancialService, FinancialError

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _require_idempotency_key(key: str | None) -> str:
    if not key or not key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    return key.strip()


def _get_owned_account(db: Session, account_id: uuid.UUID, user: User) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None or (user.role == "ACCOUNT_HOLDER" and account.user_id != user.id):
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/deposit", response_model=TransactionResponse)
def deposit(
    payload: DepositRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    account = _get_owned_account(db, payload.account_id, current_user)
    svc = FinancialService(db)
    try:
        result = svc.deposit(
            initiator=current_user,
            account_id=account.id,
            amount_paise=payload.amount_paise,
            currency=payload.currency,
            idempotency_key=key,
            request_path="/api/transactions/deposit",
            request_method="POST",
            request_payload=payload.model_dump(),
            description=payload.description,
            metadata=payload.metadata,
        )
    except FinancialError as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)
    return result.body


@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(
    payload: WithdrawRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    account = _get_owned_account(db, payload.account_id, current_user)
    svc = FinancialService(db)
    try:
        result = svc.withdraw(
            initiator=current_user,
            account_id=account.id,
            amount_paise=payload.amount_paise,
            currency=payload.currency,
            idempotency_key=key,
            request_path="/api/transactions/withdraw",
            request_method="POST",
            request_payload=payload.model_dump(),
            description=payload.description,
            metadata=payload.metadata,
        )
    except FinancialError as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)
    return result.body


@router.post("/transfer", response_model=TransactionResponse)
def transfer(
    payload: TransferRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    source = _get_owned_account(db, payload.from_account_id, current_user)
    dest = db.query(Account).filter(Account.id == payload.to_account_id).first()
    if dest is None:
        raise HTTPException(status_code=404, detail="Destination account not found")
    svc = FinancialService(db)
    try:
        result = svc.transfer(
            initiator=current_user,
            from_account_id=source.id,
            to_account_id=dest.id,
            amount_paise=payload.amount_paise,
            currency=payload.currency,
            idempotency_key=key,
            request_path="/api/transactions/transfer",
            request_method="POST",
            request_payload=payload.model_dump(),
            description=payload.description,
            metadata=payload.metadata,
        )
    except FinancialError as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)
    return result.body


@router.post("/{transaction_id}/reverse", status_code=status.HTTP_201_CREATED)
def reverse_transaction(
    transaction_id: uuid.UUID,
    payload: ReverseRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    key = _require_idempotency_key(idempotency_key)
    svc = FinancialService(db)
    try:
        result = svc.reverse(
            initiator=admin,
            original_transaction_id=transaction_id,
            reason=payload.reason,
            idempotency_key=key,
            request_path=f"/api/transactions/{transaction_id}/reverse",
            request_method="POST",
            request_payload={"transaction_id": str(transaction_id), "reason": payload.reason},
        )
    except FinancialError as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)
    return result.body
