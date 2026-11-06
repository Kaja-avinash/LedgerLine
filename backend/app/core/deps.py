"""FastAPI dependencies: authentication and RBAC."""

import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.revoked_token import RevokedToken
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate the caller from the Bearer JWT."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except Exception:
        raise credentials_exc

    sub = payload.get("sub")
    jti = payload.get("jti")
    if not sub or not jti:
        raise credentials_exc

    # Token revocation check.
    revoked = db.query(RevokedToken).filter(RevokedToken.token_jti == jti).first()
    if revoked is not None:
        raise credentials_exc

    try:
        user_id = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def has_role(user: User, *allowed_roles: str) -> bool:
    """Pure role check helper (testable without a DB session)."""
    return user.role in allowed_roles


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency factory enforcing that the current user has one of the roles."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_role(current_user, *allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation",
            )
        return current_user

    return _checker


# Convenience role guards.
require_admin = require_roles("ADMINISTRATOR")
require_account_holder = require_roles("ACCOUNT_HOLDER")
require_auditor = require_roles("AUDITOR")
require_admin_or_auditor = require_roles("ADMINISTRATOR", "AUDITOR")
require_any_authenticated = require_roles("ADMINISTRATOR", "ACCOUNT_HOLDER", "AUDITOR")
