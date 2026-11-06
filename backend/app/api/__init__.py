"""API router aggregation."""

from fastapi import APIRouter

from app.api.accounts import router as accounts_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.transactions import router as transactions_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(audit_router)
