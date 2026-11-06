"""Email sending utility using Python's built-in smtplib."""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)


def _smtp_config():
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", user or "noreply@ledgerline.local")
    return host, port, user, password, sender


def send_email(to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
    """Send an email. Returns True on success, False if SMTP not configured/failed.

    Never raises; failures are logged to stdout so registration/login still succeed.
    """
    host, port, user, password, sender = _smtp_config()
    if not user or not password:
        print(f"[email] SMTP not configured; skipping email to {to}: {subject}")
        return False

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(user, password)
                server.send_message(msg)
        print(f"[email] Sent '{subject}' to {to}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[email] Failed to send '{subject}' to {to}: {exc}")
        return False


def send_welcome_email(to: str, email: str) -> bool:
    subject = "Welcome to LedgerLine"
    text = (
        f"Hi {email},\n\n"
        "Welcome to LedgerLine — money movement with a ledger you can prove.\n\n"
        "Your account has been created successfully. You can now sign in and "
        "manage your accounts, deposits, withdrawals, and transfers.\n\n"
        "If you did not create this account, please ignore this email.\n\n"
        "— The LedgerLine Team"
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#4f46e5;">Welcome to LedgerLine</h2>
      <p>Hi <strong>{email}</strong>,</p>
      <p>Your account has been created successfully. You can now sign in and
      manage your accounts, deposits, withdrawals, and transfers.</p>
      <p style="color:#6b7280;font-size:12px;">If you did not create this
      account, please ignore this email.</p>
      <p>— The LedgerLine Team</p>
    </div>
    """
    return send_email(to, subject, text, html)


def send_otp_email(to: str, otp: str) -> bool:
    subject = "Your LedgerLine login code"
    text = (
        f"Your LedgerLine login verification code is: {otp}\n\n"
        "This code expires in 5 minutes. Do not share it with anyone.\n\n"
        "If you did not attempt to sign in, please ignore this email and "
        "consider changing your password.\n\n"
        "— The LedgerLine Team"
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#4f46e5;">Login verification</h2>
      <p>Your LedgerLine login code is:</p>
      <p style="font-size:32px;font-weight:bold;letter-spacing:6px;color:#111827;">{otp}</p>
      <p>This code expires in <strong>5 minutes</strong>. Do not share it with anyone.</p>
      <p style="color:#6b7280;font-size:12px;">If you did not attempt to sign in,
      please ignore this email.</p>
      <p>— The LedgerLine Team</p>
    </div>
    """
    return send_email(to, subject, text, html)
