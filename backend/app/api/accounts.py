"""Account management routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreateRequest, AccountResponse, AccountStatementResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def _get_account_or_404(db: Session, account_id: uuid.UUID, current_user: User) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role == "ACCOUNT_HOLDER" and account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Account]:
    q = db.query(Account)
    if current_user.role == "ACCOUNT_HOLDER":
        q = q.filter(Account.user_id == current_user.id)
    return q.order_by(Account.created_at).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Account:
    return _get_account_or_404(db, account_id, current_user)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Account:
    # Validate owner exists
    owner = db.query(User).filter(User.id == payload.user_id).first()
    if owner is None:
        raise HTTPException(status_code=404, detail="Owner user not found")
    if payload.account_type == "CUSTOMER" and owner.role != "ACCOUNT_HOLDER":
        raise HTTPException(status_code=400, detail="Customer accounts require an account holder owner")
    account = Account(
        account_number=f"ACC-{uuid.uuid4().hex[:12]}",
        user_id=payload.user_id,
        account_type=payload.account_type,
        currency=payload.currency,
        status="ACTIVE",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.post("/{account_id}/freeze", response_model=AccountResponse)
def freeze_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account.status = "FROZEN"
    db.commit()
    db.refresh(account)
    # audit
    from app.models.admin_audit_event import AdminAuditEvent

    db.add(
        AdminAuditEvent(
            admin_user_id=admin.id,
            action_type="FREEZE_ACCOUNT",
            target_resource_id=account.id,
            reason_narrative="Account frozen by administrator",
        )
    )
    db.commit()
    return account


@router.post("/{account_id}/unfreeze", response_model=AccountResponse)
def unfreeze_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account.status = "ACTIVE"
    db.commit()
    db.refresh(account)
    from app.models.admin_audit_event import AdminAuditEvent

    db.add(
        AdminAuditEvent(
            admin_user_id=admin.id,
            action_type="UNFREEZE_ACCOUNT",
            target_resource_id=account.id,
            reason_narrative="Account unfrozen by administrator",
        )
    )
    db.commit()
    return account


@router.get("/{account_id}/statement", response_model=AccountStatementResponse)
def account_statement(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    account = _get_account_or_404(db, account_id, current_user)
    # postings
    postings = db.execute(
        text(
            "SELECT 'POSTING' AS kind, entry_type, amount_paise, running_balance_paise, "
            "account_activity_sequence, created_at, transaction_id "
            "FROM ledger_entries WHERE account_id = :aid"
        ),
        {"aid": account.id},
    ).mappings().all()
    refusals = db.execute(
        text(
            "SELECT 'REFUSED' AS kind, operation_type AS entry_type, attempted_amount_paise AS amount_paise, "
            "observed_balance_paise AS running_balance_paise, account_activity_sequence, created_at, NULL AS transaction_id "
            "FROM refused_operations WHERE account_id = :aid"
        ),
        {"aid": account.id},
    ).mappings().all()

    items = sorted(list(postings) + list(refusals), key=lambda r: r["account_activity_sequence"])
    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "projected_balance_paise": account.projected_balance_paise,
        "items": [dict(r) for r in items],
    }
