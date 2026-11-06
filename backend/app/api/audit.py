"""Audit and reporting routes (admin + auditor)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin_or_auditor
from app.core.database import get_db
from app.models.admin_audit_event import AdminAuditEvent
from app.models.account import Account
from app.services.reconciliation import ReconciliationService

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/events")
def list_audit_events(
    db: Session = Depends(get_db),
    _user=Depends(require_admin_or_auditor),
):
    events = db.query(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc()).limit(200).all()
    return [
        {
            "id": str(e.id),
            "admin_user_id": str(e.admin_user_id),
            "action_type": e.action_type,
            "target_resource_id": str(e.target_resource_id),
            "reason_narrative": e.reason_narrative,
            "details": e.details,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/clearing-balances")
def clearing_balances(
    db: Session = Depends(get_db),
    _user=Depends(require_admin_or_auditor),
):
    rows = db.query(Account).filter(Account.account_type.like("SYSTEM_CLEARING_%")).all()
    return [
        {
            "account_id": str(a.id),
            "account_type": a.account_type,
            "balance_paise": a.projected_balance_paise,
        }
        for a in rows
    ]


@router.get("/reconciliation")
def reconciliation(
    db: Session = Depends(get_db),
    _user=Depends(require_admin_or_auditor),
):
    return ReconciliationService(db).run()
