"""Authentication routes."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, oauth2_scheme
from app.core.email import send_otp_email, send_welcome_email
from app.core.security import create_access_token, hash_password, verify_password
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import LoginResponse, RegisterRequest, VerifyOtpRequest
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

PUBLIC_REGISTRATION_ROLE = "ACCOUNT_HOLDER"
OTP_EXPIRY_MINUTES = 5

# Simple in-memory failed-attempt tracker for OTP verification (per process).
_otp_failures: dict[str, int] = {}
OTP_MAX_ATTEMPTS = 5


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

    # Send welcome email (best-effort; never blocks registration).
    send_welcome_email(user.email, user.email)
    return user


@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    role: str = Form("ACCOUNT_HOLDER"),
    db: Session = Depends(get_db),
):
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
    if user.role != role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Role mismatch: credentials do not match the requested role",
        )

    # Generate 6-digit OTP, hash and store with 5-minute expiry.
    otp = f"{secrets.randbelow(1000000):06d}"
    user.otp_code = hash_password(otp)
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    db.commit()

    sent = send_otp_email(user.email, otp)
    if not sent:
        print(f"[dev] OTP for {user.email}: {otp} (SMTP not configured)")

    return {"status": "otp_required", "email": user.email}


@router.post("/verify-otp", response_model=LoginResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or user.otp_code is None or user.otp_expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No pending OTP for this account",
        )
    if _otp_failures.get(payload.email, 0) >= OTP_MAX_ATTEMPTS:
        user.otp_code = None
        user.otp_expires_at = None
        db.commit()
        _otp_failures.pop(payload.email, None)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed OTP attempts",
        )
    if datetime.now(timezone.utc) > user.otp_expires_at:
        user.otp_code = None
        user.otp_expires_at = None
        db.commit()
        _otp_failures.pop(payload.email, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP expired",
        )
    if not verify_password(payload.otp, user.otp_code):
        _otp_failures[payload.email] = _otp_failures.get(payload.email, 0) + 1
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    # Clear OTP
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    _otp_failures.pop(payload.email, None)

    token, _, _ = create_access_token(user.id, user.role)
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
    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    jti = payload["jti"]
    exp = payload["exp"]
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

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
