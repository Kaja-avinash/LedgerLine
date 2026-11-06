import os
from getpass import getpass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models import Account, User


database_url = os.environ["DATABASE_URL_MIGRATOR"]

database_url = database_url.replace(
    "postgres://", "postgresql+psycopg://", 1
).replace(
    "postgresql://", "postgresql+psycopg://", 1
)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def create_user(db, email, role):
    user = db.query(User).filter(User.email == email).first()

    if user:
        if user.role != role:
            raise ValueError(f"Role mismatch for {email}")
        print(f"Existing user: {email}")
        return user

    while True:
        password = getpass(f"Create password for {email}: ")
        confirm = getpass("Confirm password: ")

        if len(password) < 12:
            print("Use at least 12 characters.")
            continue

        if password != confirm:
            print("Passwords do not match.")
            continue

        break

    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True
    )

    db.add(user)
    db.flush()

    print(f"Created: {email}")
    return user


def create_system_account(db, account_type, account_number):
    account = db.query(Account).filter(
        Account.account_type == account_type
    ).first()

    if not account:
        db.add(Account(
            account_number=account_number,
            user_id=None,
            account_type=account_type,
            currency="INR",
            status="ACTIVE",
            projected_balance_paise=0,
            last_activity_sequence=0
        ))
        print(f"Created: {account_type}")


def main():
    admin_email = input(
        "Administrator email [iamkarao@gmail.com]: "
    ).strip() or "iamkarao@gmail.com"

    holder_email = input(
        "Account Holder email [avinashkaja280@gmail.com]: "
    ).strip() or "avinashkaja280@gmail.com"

    if admin_email.lower() == holder_email.lower():
        raise ValueError("The two emails must be different.")

    db = SessionLocal()

    try:
        create_user(db, admin_email, "ADMINISTRATOR")
        holder = create_user(db, holder_email, "ACCOUNT_HOLDER")

        customer = db.query(Account).filter(
            Account.user_id == holder.id,
            Account.account_type == "CUSTOMER"
        ).first()

        if not customer:
            db.add(Account(
                account_number="ACC-AVINASH01",
                user_id=holder.id,
                account_type="CUSTOMER",
                currency="INR",
                status="ACTIVE",
                projected_balance_paise=0,
                last_activity_sequence=0
            ))
            print("Created: ACC-AVINASH01")

        create_system_account(
            db, "SYSTEM_CLEARING_DEPOSIT", "SYS-DEP-001"
        )

        create_system_account(
            db, "SYSTEM_CLEARING_WITHDRAWAL", "SYS-WDR-001"
        )

        db.commit()
        print("\nLedgerLine cloud seed completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()