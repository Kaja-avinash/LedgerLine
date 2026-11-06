"""Authentication routes."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, oauth2_scheme
from app.core.security import create_access_token, hash_password, verify_password
from app.core.database import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import LoginResponse, RegisterRequest
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

PUBLIC_REGISTRATION_ROLE = "ACCOUNT_HOLDER"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    if payload.role != PUBLIC_REGISTRATION_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration cannot assign privileged roles",
        )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=PUBLIC_REGISTRATION_ROLE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> LoginResponse:
    user = db.query(User).filter(User.email == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    token, _, expires_at = create_access_token(user.id, user.role)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> None:
    # Decode to obtain jti and exp for revocation record.
    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    jti = payload["jti"]
    exp = payload["exp"]
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    # Avoid duplicate revocation entries.
    existing = db.query(RevokedToken).filter(RevokedToken.token_jti == jti).first()
    if existing is None:
        db.add(
            RevokedToken(
                token_jti=jti,
                user_id=current_user.id,
                expires_at=expires_at,
                reason="LOGOUT",
            )
        )
        db.commit()
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
