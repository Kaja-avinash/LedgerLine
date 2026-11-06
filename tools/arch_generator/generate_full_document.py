import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from build_full_doc_helpers import (
    set_cell_background, set_cell_margins, add_callout,
    add_code_block, format_table, add_figure
)

def build_ledgerline_docx():
    doc = docx.Document()
    
    # Configure A4 Margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("LedgerLine — Final Architecture Validation & Technical Specification")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(120, 120, 120)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Page Financial Engineering Specification | Private Assessment Work | Snovasys 2026")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(140, 140, 140)

    # Document Header / Cover Meta
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("LedgerLine — Final Architecture Validation & Technical Specification")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(16, 44, 87)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run("Money movement with a ledger you can prove.\nIndividual Engineering Assessment — Snovasys | Date: 05 November 2026")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(74, 85, 104)

    add_callout(
        doc,
        "This specification establishes the authoritative, production-grade technical and architectural blueprint for LedgerLine. "
        "It defines the double-entry accounting rules, PostgreSQL ACID concurrency model, early atomic idempotency claim engine, "
        "parent-row closure locks, deferred constraint triggers, defense-in-depth authorization matrix, and automated test suite. "
        "No application implementation may deviate from the financial invariants codified in this document.",
        title="EXECUTIVE MANDATE & FINANCIAL INVARIANT DIRECTIVE",
        bg_hex="FEFCBF", border_hex="B7791F"
    )

    def add_h1(text):
        h = doc.add_heading(text, level=1)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(4)
        run = h.runs[0]
        run.font.name = "Calibri"
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = RGBColor(16, 44, 87)
        return h

    def add_h2(text):
        h = doc.add_heading(text, level=2)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(3)
        run = h.runs[0]
        run.font.name = "Calibri"
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(43, 108, 176)
        return h

    def add_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(45, 55, 72)
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.1
        r_b = p.add_run(bold_prefix)
        r_b.font.name = "Calibri"
        r_b.font.bold = True
        r_b.font.size = Pt(9.5)
        r_b.font.color.rgb = RGBColor(16, 44, 87)
        r_t = p.add_run(text)
        r_t.font.name = "Calibri"
        r_t.font.size = Pt(9.5)
        r_t.font.color.rgb = RGBColor(45, 55, 72)
        return p

    # =========================================================================
    # SECTION 1
    # =========================================================================
    add_h1("1. Final Technology Architecture & Justifications")
    add_p(
        "LedgerLine is engineered as a high-concurrency, double-entry financial transaction management system. "
        "The primary engineering objective is not merely providing an operational API, but proving absolute financial correctness: "
        "money is strictly conserved, transactions execute atomically, duplicate client submissions never pay twice, and concurrent "
        "withdrawals can never drive an account balance negative. Every architectural layer is selected to enforce these guarantees."
    )

    t1_headers = ["Layer / Component", "Technology Choice", "Architectural Justification & Role"]
    t1_widths = [1.8, 1.8, 2.6]
    t1_data = [
        ["API & Transport Engine", "Python 3.11+ / FastAPI", "Asynchronous runtime, native OpenAPI 3.1 schema generation, dependency injection for security/DB."],
        ["Data Validation", "Pydantic v2", "Strict schema sanitization at API perimeter; enforces positive integer minor units (paise) and rejects floats."],
        ["ORM & Connection Layer", "SQLAlchemy 2.0 / Alembic", "Explicit session management (async with session.begin()), row-level locks, versioned migrations."],
        ["Database Engine", "PostgreSQL 15+", "ACID compliance, READ COMMITTED with SELECT FOR UPDATE, deferred constraint triggers, PL/pgSQL immutability."],
        ["Client Presentation", "React 18 / TypeScript / Vite", "Deterministic UUIDv4 idempotency generation, type-safe API consumption, role-tailored dashboards."],
        ["Test Infrastructure", "Pytest / HTTPX / asyncpg", "asyncio.Barrier concurrent request synchronization against an actual PostgreSQL connection pool."]
    ]
    tbl1 = doc.add_table(rows=len(t1_data)+1, cols=3)
    format_table(tbl1, t1_widths, t1_headers, t1_data)
    add_figure(doc, "temp_diagrams/diagram_1_overall_architecture.png", "Figure 1: Overall System Architecture, Layer Boundaries & Database Triggers")

    # =========================================================================
    # SECTION 2
    # =========================================================================
    add_h1("2. System Architecture, Actors & Component Boundaries")
    add_p(
        "The application architecture strictly decouples transport parsing, authentication, role authorization, resource ownership, "
        "transaction coordination, and ledger persistence. System actors interact exclusively through authenticated REST endpoints "
        "governed by defense-in-depth guards."
    )
    add_bullet("Administrator: ", "System management, user onboarding, customer account creation, account freezing/unfreezing, transaction reversals, operational audits.")
    add_bullet("Account Holder: ", "Personal account inspection, balance queries, transaction statements, simulated deposits, withdrawals, and internal transfers.")
    add_bullet("Auditor: ", "Strictly read-only access to all accounts, balances, immutable ledger entries, refusal logs, and real-time reconciliation reports.")
    add_figure(doc, "temp_diagrams/diagram_2_component_boundaries.png", "Figure 2: System Actors, Security Boundary, Domain Engines & Relational Data Stores")

    # =========================================================================
    # SECTION 3
    # =========================================================================
    add_h1("3. Detailed Component Responsibilities & Interface Contracts")
    add_p(
        "To prevent architectural blurring and ensure testability, each service component operates under explicit, non-overlapping boundaries:"
    )
    add_bullet("API Routers (`app.api`): ", "Parse incoming HTTP requests, validate headers (including mandatory Idempotency-Key), delegate to domain services, and serialize JSON responses. Absolutely no direct balance checks or financial mutations occur in routers.")
    add_bullet("Security Middleware (`app.core.security`): ", "Verifies JWT cryptographic signatures, checks expiration (`exp`), verifies token has not been revoked against `revoked_tokens`, and validates that `user.is_active == TRUE`.")
    add_bullet("Idempotency Service (`app.services.idempotency`): ", "Computes SHA-256 canonical fingerprints, executes early atomic claims using PostgreSQL unique index locks, catches concurrent collisions, and returns cached terminal responses.")
    add_bullet("Transaction Coordinator (`app.services.transfer_svc`): ", "Enforces deterministic account lock ordering, acquires `SELECT ... FOR UPDATE` row locks, manages the parent transaction header lifecycle, and coordinates balanced ledger postings.")
    add_bullet("Ledger Engine (`app.services.ledger_engine`): ", "Calculates account-specific activity sequences, updates transactionally projected balances, and generates balanced debit/credit posting pairs according to account normal balance sides.")
    add_bullet("Reconciliation Engine (`app.services.reconcile`): ", "Executes independent 4-way mathematical verification across all account classifications without modifying database state.")

    # =========================================================================
    # SECTION 4
    # =========================================================================
    add_h1("4. Accounting Model & Normal Balance Sides")
    add_p(
        "LedgerLine adheres strictly to standard financial double-entry accounting conventions. Every account classification possesses a defined "
        "perspective, normal balance side, and calculation formula. Floating-point numbers are prohibited across all layers; all monetary arithmetic "
        "is conducted strictly in integer minor units (paise, where ₹1.00 = 100 paise)."
    )

    t4_headers = ["Account Classification", "Perspective", "Normal Balance", "Balance Calculation Formula", "Database Constraint Rules"]
    t4_widths = [1.6, 1.2, 1.0, 1.4, 1.8]
    t4_data = [
        ["Customer Accounts (`CUSTOMER`)", "Platform Liability", "CREDIT", "Balance = Credits - Debits", "CHECK (projected_balance_paise >= 0) strictly enforced."],
        ["Deposit Clearing (`SYSTEM_CLEARING_DEPOSIT`)", "Asset / Source", "DEBIT", "Balance = Debits - Credits", "Tracks cumulative gross inbound volume. Unconstrained."],
        ["Withdrawal Clearing (`SYSTEM_CLEARING_WITHDRAWAL`)", "Liability / Sink", "CREDIT", "Balance = Credits - Debits", "Tracks cumulative gross disbursements. Unconstrained."]
    ]
    tbl4 = doc.add_table(rows=len(t4_data)+1, cols=5)
    format_table(tbl4, t4_widths, t4_headers, t4_data)

    # =========================================================================
    # SECTION 5
    # =========================================================================
    add_h1("5. Financial Invariants & Conservation Equation")
    add_p(
        "The system enforces two foundational mathematical invariants that govern all money movement:"
    )
    add_h2("Invariant 1: Transaction Balance Equality")
    add_p(
        "For every completed financial transaction T, the sum of all debit postings must exactly equal the sum of all credit postings. "
        "No transaction may possess an odd number of entries or unequal amounts:"
    )
    add_code_block(doc, "SUM(amount_paise WHERE entry_type = 'DEBIT') == SUM(amount_paise WHERE entry_type = 'CREDIT')")

    add_h2("Invariant 2: Platform Conservation of Money")
    add_p(
        "Customer balances can change exclusively through documented external deposits, external withdrawals, and their authorized reversals. "
        "Arbitrary administrator adjustments that unilaterally inflate or deflate customer balances are prohibited. Internal transfers have a net customer impact of exactly zero:"
    )
    add_code_block(doc, "Total Closing Customer Balances = Total Opening Customer Balances + Net Deposits - Net Withdrawals\n"
                        "Where Net Deposits = Gross Deposits - Reversed Deposits\n"
                        "Where Net Withdrawals = Gross Withdrawals - Reversed Withdrawals")

    # =========================================================================
    # SECTION 6
    # =========================================================================
    add_h1("6. Financial Operations: Postings & Reversals")
    add_p(
        "All four core financial operations generate balanced double-entry ledger postings:"
    )
    add_bullet("Simulated External Deposit: ", "Debits `SYSTEM_CLEARING_DEPOSIT` (Asset increases), Credits `Customer Account` (Customer Liability increases). Customer balance increases.")
    add_bullet("Simulated External Withdrawal: ", "Debits `Customer Account` (Customer Liability decreases), Credits `SYSTEM_CLEARING_WITHDRAWAL` (Disbursement increases). Customer balance decreases.")
    add_bullet("Internal Account Transfer: ", "Debits `Source Customer Account` (-amount), Credits `Destination Customer Account` (+amount). Net customer change is exactly ₹0.")
    add_bullet("Compensating Transaction Reversal: ", "Creates a new transaction referencing `reverses_transaction_id`, generating exact inverted postings (Debits <-> Credits) for the identical accounts and amounts.")
    add_figure(doc, "temp_diagrams/diagram_3_double_entry_operations.png", "Figure 3: Double-Entry Postings Across Deposit, Withdrawal, Transfer and Reversal Operations")

    # =========================================================================
    # SECTION 7
    # =========================================================================
    add_h1("7. PostgreSQL Relational Database Schema")
    add_p(
        "The database schema is partitioned into eight specialized tables with independent lifecycles and append-only immutability triggers:"
    )
    add_code_block(doc, """-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Users Table (Identity & RBAC)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL, -- 'ADMINISTRATOR', 'ACCOUNT_HOLDER', 'AUDITOR'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 2. Accounts Table (Customer & System Clearing Accounts)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number VARCHAR(32) UNIQUE NOT NULL,
    user_id UUID NULL REFERENCES users(id) ON DELETE RESTRICT,
    account_type VARCHAR(32) NOT NULL, -- 'CUSTOMER', 'SYSTEM_CLEARING_DEPOSIT', 'SYSTEM_CLEARING_WITHDRAWAL'
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'FROZEN', 'CLOSED'
    projected_balance_paise BIGINT NOT NULL DEFAULT 0,
    last_activity_sequence BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_currency_inr CHECK (currency = 'INR'),
    CONSTRAINT chk_customer_balance_non_negative CHECK (
        account_type != 'CUSTOMER' OR projected_balance_paise >= 0
    )
);

-- 3. Financial Transactions Table (Controlled Closure Header)
CREATE TABLE financial_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_type VARCHAR(32) NOT NULL, -- 'DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'REVERSAL'
    initiator_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    reference_id VARCHAR(64) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,
    posted_at TIMESTAMP WITH TIME ZONE NULL,
    reverses_transaction_id UUID NULL REFERENCES financial_transactions(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_single_transaction_reversal 
ON financial_transactions (reverses_transaction_id) 
WHERE reverses_transaction_id IS NOT NULL;

-- 4. Ledger Entries Table (Strictly Append-Only Double-Entry Postings)
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES financial_transactions(id) ON DELETE RESTRICT,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    entry_type VARCHAR(16) NOT NULL, -- 'DEBIT', 'CREDIT'
    amount_paise BIGINT NOT NULL CHECK (amount_paise > 0),
    account_activity_sequence BIGINT NOT NULL,
    running_balance_paise BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_ledger_sequence UNIQUE (account_id, account_activity_sequence)
);

-- 5. Idempotency Records Table (Atomic Key Claim & Terminal State Cache)
CREATE TABLE idempotency_records (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    key VARCHAR(255) NOT NULL,
    request_path VARCHAR(255) NOT NULL,
    request_method VARCHAR(16) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'IN_PROGRESS', -- 'IN_PROGRESS', 'COMPLETED', 'REFUSED'
    response_status_code INTEGER NULL,
    response_body JSONB NULL,
    transaction_id UUID NULL REFERENCES financial_transactions(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, key)
);

-- 6. Refused Operations Table (Authorized Business Rejection Audit)
CREATE TABLE refused_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    observed_balance_paise BIGINT NOT NULL,
    account_activity_sequence BIGINT NOT NULL,
    operation_type VARCHAR(32) NOT NULL,
    attempted_amount_paise BIGINT NOT NULL,
    reason_code VARCHAR(64) NOT NULL, -- 'INSUFFICIENT_FUNDS', 'ACCOUNT_FROZEN', 'SELF_TRANSFER'
    reason_message TEXT NOT NULL,
    idempotency_key VARCHAR(255) NULL,
    request_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_refused_sequence UNIQUE (account_id, account_activity_sequence)
);

-- 7. Admin Audit Events Table (Privileged Action & Security Audit Log)
CREATE TABLE admin_audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action_type VARCHAR(64) NOT NULL, -- 'FREEZE_ACCOUNT', 'UNFREEZE_ACCOUNT', 'CREATE_ACCOUNT', 'UNAUTHORIZED_ACCESS_ATTEMPT'
    target_resource_id UUID NOT NULL,
    reason_narrative TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 8. Revoked Tokens Table (Authentication Revocation)
CREATE TABLE revoked_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_jti VARCHAR(64) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reason VARCHAR(64) NOT NULL DEFAULT 'LOGOUT'
);
CREATE INDEX idx_revoked_tokens_jti ON revoked_tokens (token_jti);""")
    add_figure(doc, "temp_diagrams/diagram_9_er_diagram.png", "Figure 4: PostgreSQL Relational Entity-Relationship Diagram")

    # =========================================================================
    # SECTION 8
    # =========================================================================
    add_h1("8. Double-Entry Database-Level Validation & Stale Event Resolution")
    add_p(
        "A critical flaw in standard database trigger design is reliance on the trigger event's `NEW` row image. When a financial transaction "
        "header is inserted with `is_closed = FALSE` and subsequently updated to `TRUE` within the same transaction, a deferred `INSERT` trigger "
        "can evaluate the obsolete initial state. To resolve this, LedgerLine's deferred trigger queries the current live row state by primary key at `COMMIT` time:"
    )
    add_code_block(doc, """CREATE OR REPLACE FUNCTION verify_financial_transaction_closure()
RETURNS TRIGGER AS $$
DECLARE
    v_is_closed BOOLEAN;
    v_debit_total BIGINT;
    v_credit_total BIGINT;
    v_posting_count INTEGER;
BEGIN
    -- Query current live row state to eliminate stale NEW event image
    SELECT is_closed INTO v_is_closed
    FROM financial_transactions
    WHERE id = NEW.id;

    IF v_is_closed IS NULL OR NOT v_is_closed THEN
        RAISE EXCEPTION 'Double-entry violation: Financial transaction % was not marked closed (is_closed=TRUE) before commit.', 
            NEW.id;
    END IF;

    -- Aggregate complete postings
    SELECT 
        COALESCE(SUM(CASE WHEN entry_type = 'DEBIT' THEN amount_paise ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN entry_type = 'CREDIT' THEN amount_paise ELSE 0 END), 0),
        COUNT(*)
    INTO v_debit_total, v_credit_total, v_posting_count
    FROM ledger_entries
    WHERE transaction_id = NEW.id;

    IF v_posting_count < 2 THEN
        RAISE EXCEPTION 'Double-entry violation: Financial transaction % has % posting(s). Minimum 2 balanced postings required.', 
            NEW.id, v_posting_count;
    END IF;

    IF v_debit_total <> v_credit_total THEN
        RAISE EXCEPTION 'Double-entry violation: Financial transaction % does not balance (Debits: %, Credits: %).', 
            NEW.id, v_debit_total, v_credit_total;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_verify_financial_transaction_closure
AFTER INSERT OR UPDATE ON financial_transactions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION verify_financial_transaction_closure();""")

    # =========================================================================
    # SECTION 9
    # =========================================================================
    add_h1("9. Financial Transaction Header Lifecycle & Parent-Row Locking")
    add_p(
        "To prevent race conditions where a concurrent worker attempts to append a ledger posting while a transaction is closing, "
        "the posting insertion trigger enforces parent-row locking using `SELECT ... FOR UPDATE` on `financial_transactions`:"
    )
    add_code_block(doc, """CREATE OR REPLACE FUNCTION prevent_posting_to_closed_transaction()
RETURNS TRIGGER AS $$
DECLARE
    v_is_closed BOOLEAN;
BEGIN
    -- Parent-row locking strategy: lock header FOR UPDATE to eliminate concurrency races
    SELECT is_closed INTO v_is_closed
    FROM financial_transactions
    WHERE id = NEW.transaction_id
    FOR UPDATE;

    IF v_is_closed IS NULL THEN
        RAISE EXCEPTION 'Foreign key violation: Parent transaction % does not exist.', NEW.transaction_id;
    END IF;

    IF v_is_closed THEN
        RAISE EXCEPTION 'Immutability violation: Cannot append ledger entry % to transaction % because it is already closed.',
            NEW.id, NEW.transaction_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_posting_to_closed_transaction
BEFORE INSERT ON ledger_entries
FOR EACH ROW
EXECUTE FUNCTION prevent_posting_to_closed_transaction();

-- Immutability Trigger: Header allows exactly one transition from FALSE -> TRUE
CREATE OR REPLACE FUNCTION protect_financial_transaction_header()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_closed THEN
        RAISE EXCEPTION 'Immutability violation: Closed financial transaction % cannot be modified or reopened.', OLD.id;
    END IF;

    IF NOT OLD.is_closed AND NEW.is_closed THEN
        -- Allow ONLY setting is_closed = TRUE and posted_at = NOW()
        IF NEW.transaction_type <> OLD.transaction_type OR 
           NEW.initiator_user_id <> OLD.initiator_user_id OR 
           NEW.reference_id <> OLD.reference_id THEN
            RAISE EXCEPTION 'Immutability violation: Core financial transaction attributes cannot be altered during closure.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_financial_transaction_header
BEFORE UPDATE ON financial_transactions
FOR EACH ROW
EXECUTE FUNCTION protect_financial_transaction_header();""")

    # =========================================================================
    # SECTION 10
    # =========================================================================
    add_h1("10. Idempotency Terminal State Validation")
    add_p(
        "To guarantee that an `IN_PROGRESS` idempotency record can never be committed to the database, a deferred constraint trigger queries "
        "the live record at `COMMIT` time and verifies that a terminal state (`COMPLETED` or `REFUSED`) and non-null HTTP response payloads are present:"
    )
    add_code_block(doc, """CREATE OR REPLACE FUNCTION verify_idempotency_terminal_state()
RETURNS TRIGGER AS $$
DECLARE
    v_status VARCHAR(32);
    v_code INTEGER;
    v_body JSONB;
    v_tx_id UUID;
BEGIN
    -- Query live row by composite primary key (user_id, key)
    SELECT status, response_status_code, response_body, transaction_id
    INTO v_status, v_code, v_body, v_tx_id
    FROM idempotency_records
    WHERE user_id = NEW.user_id AND key = NEW.key;

    IF v_status NOT IN ('COMPLETED', 'REFUSED') THEN
        RAISE EXCEPTION 'Idempotency violation: Record for key % (user %) cannot commit with non-terminal status %.', 
            NEW.key, NEW.user_id, v_status;
    END IF;

    IF v_code IS NULL OR v_body IS NULL THEN
        RAISE EXCEPTION 'Idempotency violation: Record for key % (user %) must contain non-null response_status_code and response_body upon commit.', 
            NEW.key, NEW.user_id;
    END IF;

    IF v_status = 'COMPLETED' AND v_tx_id IS NULL THEN
        RAISE EXCEPTION 'Idempotency violation: Completed financial record for key % must reference a valid transaction_id.',
            NEW.key;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_verify_idempotency_terminal_state
AFTER INSERT OR UPDATE ON idempotency_records
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION verify_idempotency_terminal_state();

-- Immutability Trigger: Completed / Refused records can NEVER be modified or deleted
CREATE OR REPLACE FUNCTION protect_completed_idempotency_record()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IN ('COMPLETED', 'REFUSED') THEN
        RAISE EXCEPTION 'Immutability violation: Finalized idempotency record for key % cannot be modified or deleted.', OLD.key;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_completed_idempotency_record
BEFORE UPDATE OR DELETE ON idempotency_records
FOR EACH ROW
EXECUTE FUNCTION protect_completed_idempotency_record();""")

    # =========================================================================
    # SECTION 11
    # =========================================================================
    add_h1("11. Early Atomic Idempotency Claiming & Replay Handling")
    add_p(
        "Instead of checking for a key, moving funds, and inserting an idempotency record at the end, LedgerLine implements early atomic claiming. "
        "The very first SQL operation inside the transaction attempts to claim the key using PostgreSQL's row-level unique index:"
    )
    add_code_block(doc, """INSERT INTO idempotency_records (
    user_id, key, request_path, request_method, request_hash, status
)
VALUES (
    :user_id, :key, :request_path, :request_method, :request_hash, 'IN_PROGRESS'
)
ON CONFLICT (user_id, key) DO NOTHING
RETURNING user_id, key;""")
    add_p(
        "If the query returns a row, the request owns the key and proceeds with financial execution. If the query returns zero rows, the key already exists "
        "or is currently being processed by another worker."
    )

    # =========================================================================
    # SECTION 12
    # =========================================================================
    add_h1("12. Concurrent Idempotency Execution under READ COMMITTED")
    add_p(
        "When two identical requests R1 and R2 arrive simultaneously under PostgreSQL READ COMMITTED isolation:"
    )
    add_bullet("1. ", "R1 enters Tx 1; R2 enters Tx 2. Both attempt `INSERT INTO idempotency_records ... ON CONFLICT DO NOTHING`.")
    add_bullet("2. ", "Tx 1 inserts the uncommitted row under unique constraint lock. Tx 2's insert automatically BLOCKS in PostgreSQL waiting for Tx 1 to resolve.")
    add_bullet("3. If Tx 1 Commits: ", "Tx 2 unblocks immediately. `ON CONFLICT DO NOTHING` returns 0 rows. Tx 2 queries the committed record, verifies payload hashes match, and returns the cached HTTP response with `Idempotent-Replay: true`. Zero financial mutations occur.")
    add_bullet("4. If Tx 1 Aborts: ", "Tx 2 unblocks. The uncommitted row disappears. Tx 2's insert succeeds, returning the claimed key. Tx 2 becomes the primary executor.")
    add_figure(doc, "temp_diagrams/diagram_5_concurrent_idempotency.png", "Figure 5: Concurrent Idempotency Key Claiming under PostgreSQL READ COMMITTED")

    # =========================================================================
    # SECTION 13
    # =========================================================================
    add_h1("13. Exact Financial Transaction Execution Sequence")
    add_p(
        "The complete lifecycle of a financial transaction follows a strict 12-step deterministic sequence:"
    )
    add_figure(doc, "temp_diagrams/diagram_4_transaction_sequence.png", "Figure 6: Step-by-Step Financial Transaction Execution Sequence")

    # =========================================================================
    # SECTION 14
    # =========================================================================
    add_h1("14. Deterministic Account Locking & Deadlock Recovery")
    add_p(
        "To prevent cross-account deadlocks during simultaneous opposing transfers (A -> B and B -> A), all modified accounts (customer and clearing) "
        "are locked in strict ascending lexicographical order of their UUIDs:"
    )
    add_code_block(doc, """async def acquire_deterministic_account_locks(session: AsyncSession, account_ids: list[UUID]) -> dict[UUID, Account]:
    # Sort IDs ascending to eliminate circular wait deadlocks
    sorted_ids = sorted(list(set(account_ids)))
    locked_accounts = {}
    for aid in sorted_ids:
        query = select(Account).where(Account.id == aid).with_for_update()
        result = await session.execute(query)
        account = result.scalar_one_or_none()
        if not account:
            raise AccountNotFoundException(f"Account {aid} does not exist.")
        locked_accounts[aid] = account
    return locked_accounts""")
    add_p(
        "Bounded Deadlock Recovery: While deterministic row ordering prevents application deadlocks, database engines can still experience deadlocks "
        "from internal index page locks. The database wrapper intercepts PostgreSQL error code `40P01` (`DeadlockDetected`) and retries up to 3 times "
        "with randomized exponential jitter (20ms, 50ms, 100ms) before reporting failure."
    )

    # =========================================================================
    # SECTION 15
    # =========================================================================
    add_h1("15. Defense-in-Depth Authentication & Authorization Architecture")
    add_p(
        "Authorization is enforced across four independent layers. Even if an attacker bypasses the client or route guard, the financial service layer "
        "validates account ownership and account status on the locked database row inside the transaction:"
    )
    add_figure(doc, "temp_diagrams/diagram_6_defense_in_depth.png", "Figure 7: Four-Layer Defense-in-Depth Security & Authorization Architecture")

    # =========================================================================
    # SECTION 16
    # =========================================================================
    add_h1("16. Complete Role & Permission Matrix")
    add_p(
        "Strict separation of duties is enforced across all roles. Administrators cannot withdraw customer funds or perform unauthorized customer transfers:"
    )

    t16_headers = ["Operational Endpoint", "Administrator", "Account Holder", "Auditor", "Enforcement Mechanism"]
    t16_widths = [1.8, 1.2, 1.3, 1.0, 1.7]
    t16_data = [
        ["User Management (`/users`)", "Full Access", "Denied", "Denied", "RoleChecker([ADMINISTRATOR])"],
        ["Create Customer Account (`/accounts`)", "Full Access", "Denied", "Denied", "RoleChecker([ADMINISTRATOR])"],
        ["Freeze / Unfreeze Account", "Full (Audited)", "Denied", "Denied", "RoleChecker([ADMINISTRATOR]) + Audit Log"],
        ["View Personal Statements", "Denied", "Owned Only", "Denied", "AccountOwnerChecker(strict=True)"],
        ["Simulated Deposit", "Denied", "Owned Only", "Denied", "AccountOwnerChecker() + Simulated Tag"],
        ["Simulated Withdrawal", "DENIED", "Owned Only", "Denied", "AccountOwnerChecker() + Balance Check"],
        ["Internal Transfer", "DENIED", "Owned Source", "Denied", "AccountOwnerChecker() on from_account"],
        ["Transaction Reversal", "Authorized Only", "Denied", "Denied", "RoleChecker([ADMINISTRATOR]) + Reason Narrative"],
        ["Inspect Ledger / Reconciliation", "Full Access", "Denied", "Read-Only", "RoleChecker([ADMINISTRATOR, AUDITOR])"]
    ]
    tbl16 = doc.add_table(rows=len(t16_data)+1, cols=5)
    format_table(tbl16, t16_widths, t16_headers, t16_data)

    # =========================================================================
    # SECTION 17
    # =========================================================================
    add_h1("17. Refused-Operation Balance History & Security Boundary")
    add_p(
        "A critical requirement of the assessment is that account statements must display refused attempts with the resulting running balance "
        "and initiating user, without polluting the double-entry financial ledger. To accomplish this, `refused_operations` records the "
        "`observed_balance_paise` and shares a monotonic `account_activity_sequence` with `ledger_entries`."
    )
    add_callout(
        doc,
        "SECURITY BOUNDARY DISTINCTION: "
        "1. Authorized Business Refusals: When the legitimate owner of Account A attempts an operation that fails business checks (e.g. Insufficient Funds), "
        "it is logged in `refused_operations` with `account_id`, `observed_balance_paise`, and `account_activity_sequence`. This allows the owner to view the refused attempt in their statement.\n"
        "2. Unauthorized Cross-Account Attacks: When User B attempts to access or withdraw from Account A without authorization (BOLA / IDOR attack), "
        "recording this in Account A's statement would leak private information. Instead, unauthorized attacks are logged in `admin_audit_events` "
        "with `action_type = 'UNAUTHORIZED_ACCESS_ATTEMPT'`, logging User B's IP and user_id without disclosing Account A's balance or internal activity sequence.",
        title="SECURITY AUDIT VS ACCOUNT STATEMENT BOUNDARY",
        bg_hex="EBF8FF", border_hex="3182CE"
    )

    # =========================================================================
    # SECTION 18
    # =========================================================================
    add_h1("18. Unified Account Activity Sequence & Statement Generation")
    add_p(
        "To eliminate dependency on wall-clock timestamps and guarantee deterministic chronological ordering under high concurrency, "
        "each account maintains an atomic, monotonically increasing `account_activity_sequence`. This sequence is incremented under row-level lock:"
    )
    add_code_block(doc, """# In active transaction under SELECT ... FOR UPDATE on accounts:
next_sequence = account.last_activity_sequence + 1
account.last_activity_sequence = next_sequence

# In ledger_entries or refused_operations:
# account_activity_sequence = next_sequence

-- Statement generation query orders strictly by activity sequence:
SELECT 'POSTING' as kind, entry_type, amount_paise, running_balance_paise, account_activity_sequence, created_at
FROM ledger_entries WHERE account_id = :aid
UNION ALL
SELECT 'REFUSED' as kind, operation_type, attempted_amount_paise, observed_balance_paise, account_activity_sequence, created_at
FROM refused_operations WHERE account_id = :aid
ORDER BY account_activity_sequence ASC;""")

    # =========================================================================
    # SECTION 19
    # =========================================================================
    add_h1("19. Exact Reversal Validation & Compensating Postings")
    add_p(
        "Reversals are executed as new compensating financial transactions. Version one strictly supports full reversals:"
    )
    add_bullet("1. Reversal Legality: ", "The original transaction must be completed and must NOT be a reversal (`reverses_transaction_id IS NULL`).")
    add_bullet("2. Single Reversal: ", "Enforced by database constraint `uq_single_transaction_reversal` on `financial_transactions(reverses_transaction_id)`.")
    add_bullet("3. Exact Compensating Postings: ", "For every original posting (account, amount, entry_type), the reversal generates an entry for the exact same account and amount with inverted entry type (`DEBIT` <-> `CREDIT`).")
    add_bullet("4. Customer Balance Sufficiency: ", "If reversing a deposit, the customer account will be debited. The engine verifies `customer.projected_balance_paise >= amount`. If the customer already spent the funds, the reversal is rejected with HTTP 400 (`INSUFFICIENT_FUNDS_FOR_REVERSAL`) to prevent driving customer balances negative.")
    add_figure(doc, "temp_diagrams/diagram_7_reversal_validation.png", "Figure 8: Reversal Validation & Compensating Postings Workflow")

    # =========================================================================
    # SECTION 20
    # =========================================================================
    add_h1("20. Multi-Account 4-Way Reconciliation Engine")
    add_p(
        "An independent, read-only reconciliation service verifies mathematical consistency across all accounts:"
    )
    add_bullet("1. Customer Liability Reconciliation: ", "Verifies `Credits - Debits == projected_balance_paise` for every customer account.")
    add_bullet("2. Deposit Clearing Asset Reconciliation: ", "Verifies `Debits - Credits == projected_balance_paise` for `SYSTEM_CLEARING_DEPOSIT`.")
    add_bullet("3. Withdrawal Clearing Liability Reconciliation: ", "Verifies `Credits - Debits == projected_balance_paise` for `SYSTEM_CLEARING_WITHDRAWAL`.")
    add_bullet("4. Platform Conservation Verification: ", "Verifies that total customer balances equal initial balances + net deposits - net withdrawals.")
    add_figure(doc, "temp_diagrams/diagram_8_reconciliation_process.png", "Figure 9: Multi-Account 4-Way Reconciliation Audit Process")

    # =========================================================================
    # SECTION 21
    # =========================================================================
    add_h1("21. Append-Only Ledger & Immutability Audit Triggers")
    add_p(
        "PostgreSQL triggers prohibit `UPDATE` and `DELETE` operations on historical financial and audit tables:"
    )
    add_code_block(doc, """CREATE OR REPLACE FUNCTION trg_enforce_immutable_financial_records()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability violation: % operation is strictly prohibited on table %.',
        TG_OP, TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_ledger_entries
BEFORE UPDATE OR DELETE ON ledger_entries
FOR EACH ROW EXECUTE FUNCTION trg_enforce_immutable_financial_records();

CREATE TRIGGER trg_protect_refused_operations
BEFORE UPDATE OR DELETE ON refused_operations
FOR EACH ROW EXECUTE FUNCTION trg_enforce_immutable_financial_records();

CREATE TRIGGER trg_protect_admin_audit_events
BEFORE UPDATE OR DELETE ON admin_audit_events
FOR EACH ROW EXECUTE FUNCTION trg_enforce_immutable_financial_records();""")

    # =========================================================================
    # SECTION 22
    # =========================================================================
    add_h1("22. Comprehensive Security Threat Register")
    add_p(
        "The project maintains an active threat register (`THREATS.md`) connecting every attack scenario to its concrete mitigation and automated test proof:"
    )

    t22_headers = ["Threat ID", "Attack Vector & Scenario", "Potential Impact", "Implemented Mitigation", "Automated Verification Test"]
    t22_widths = [1.1, 1.8, 1.3, 1.8, 1.8]
    t22_data = [
        ["T-01", "10 concurrent withdrawals of ₹800 against ₹1,000 balance.", "Negative balance, money creation.", "SELECT FOR UPDATE row locks + CHECK (balance >= 0).", "test_concurrent_withdrawals_prevent_overdraft"],
        ["T-02", "Concurrent transfers A->B and B->A cause deadlocks.", "500 error, transaction abort.", "Ascending UUID lock ordering + retry on 40P01.", "test_opposing_transfers_no_deadlock"],
        ["T-03", "Network timeout after debit; client resends transfer.", "Duplicate debit / payment.", "Early atomic claim via INSERT ON CONFLICT DO NOTHING.", "test_replayed_transfer_returns_original"],
        ["T-04", "Attacker replays key K with altered amount or recipient.", "Fraudulent transfer.", "SHA-256 canonical hash comparison; returns 422.", "test_idempotency_payload_mutation_rejected"],
        ["T-05", "User A modifies account_id to User B's account in withdrawal.", "Theft of third-party funds.", "Server-side account.user_id == current_user.id check.", "test_cross_account_withdrawal_rejected_403"],
        ["T-06", "Attacker or admin executes direct SQL UPDATE on ledger.", "Audit trail destruction.", "BEFORE UPDATE/DELETE triggers throwing exceptions.", "test_ledger_immutability_trigger"],
        ["T-07", "Administrator attempts direct withdrawal from customer.", "Administrative siphoning.", "RBAC blocking admins from customer withdrawal APIs.", "test_admin_cannot_withdraw_customer_funds"],
        ["T-08", "Database crashes after debit before credit insertion.", "Money destroyed; unbalanced.", "Single atomic database transaction (session.begin()).", "test_transfer_partial_failure_rollback"],
        ["T-09", "Buggy code commits transaction with unequal debits/credits.", "Unbalanced books.", "Deferred trigger verify_financial_transaction_closure.", "test_unbalanced_transaction_rejected"],
        ["T-10", "Admin attempts duplicate reversal of same transaction.", "Double compensation.", "Partial unique index uq_single_transaction_reversal.", "test_duplicate_reversal_rejected"]
    ]
    tbl22 = doc.add_table(rows=len(t22_data)+1, cols=5)
    format_table(tbl22, t22_widths, t22_headers, t22_data)

    # =========================================================================
    # SECTION 23
    # =========================================================================
    add_h1("23. Real PostgreSQL Automated Concurrency & Failure Recovery Tests")
    add_p(
        "All concurrency and integrity tests execute against an actual PostgreSQL database instance using independent connection pool sessions "
        "and `asyncio.Barrier` synchronization:"
    )
    add_bullet("1. Mandatory Concurrent Overdraft Test: ", "Account initialized with ₹1,000. 10 concurrent requests of ₹800 synchronized via `asyncio.Barrier(10)`. Exactly 1 request returns HTTP 200; exactly 9 return HTTP 400 (`INSUFFICIENT_FUNDS`). Final balance is exactly ₹200. Exactly 1 debit and 1 credit posting exist in `ledger_entries`. Exactly 9 refusal rows exist in `refused_operations`.")
    add_bullet("2. Mandatory Identical Idempotency Key Test: ", "Sender with ₹500, recipient with ₹0. 5 concurrent requests with identical key K and amount ₹300 via `asyncio.Barrier(5)`. Exactly one transfer transaction executes. All 5 workers receive identical HTTP 200 responses with the same `transaction_id`. Sender closing balance: ₹200; recipient closing balance: ₹300.")
    add_bullet("3. Opposing Cross-Transfer Test: ", "Account A (₹10,000) and Account B (₹10,000). 20 concurrent tasks (10 transferring A->B, 10 transferring B->A). 100% of transfers complete successfully without unhandled deadlocks. Total money conserved across both accounts remains exactly ₹20,000.")
    add_bullet("4. Partial Failure & Rollback Test: ", "Simulate exception prior to transaction closure. Entire transaction rolls back; zero ledger rows created; sender balance unchanged.")
    add_bullet("5. Incomplete Header Rejection Test: ", "Insert `financial_transactions` without postings. At commit, deferred trigger throws exception and rolls back transaction.")
    add_bullet("6. Token Revocation Test: ", "User logs out, inserting JWT JTI into `revoked_tokens`. Subsequent requests with the token are rejected with HTTP 401.")

    # =========================================================================
    # SECTION 24
    # =========================================================================
    add_h1("24. Git Policy, Seven-Day Roadmap & Accepted Limitations")
    add_p(
        "Git & Repository Workflow: The GitHub repository remains strictly PRIVATE throughout development (Nov 5 to Nov 12). "
        "Automatic commits and automatic pushes to the private repository are authorized for logically completed, verified milestones. "
        "Public publication is reserved exclusively for the authorized final submission stage, following placement-cell clarification and explicit user approval."
    )
    add_h2("Seven-Day Development Roadmap")
    add_bullet("Day 1 (Nov 5): ", "Milestone 1 — Architecture Approval, Project Scaffolding, Alembic Migrations, Invariant Triggers.")
    add_bullet("Day 2 (Nov 6): ", "Milestone 2 — Authentication, Token Revocation, RBAC, BOLA Account Ownership Guards & Tests.")
    add_bullet("Day 3 (Nov 7): ", "Milestone 3 — Core Financial Engine, Double-Entry Postings, Simulated Cash Flow, Balance Projections.")
    add_bullet("Day 4 (Nov 8): ", "Milestone 4 — Concurrency Row-Level Locking, Early Idempotency Claiming, Parent-Row Closure.")
    add_bullet("Day 5 (Nov 9): ", "Milestone 5 — Security Hardening, Automated Concurrency Stress Tests (Overdraft, Replays, Deadlocks).")
    add_bullet("Day 6 (Nov 10): ", "Milestone 6 — React Dashboards (Admin, Holder, Auditor), Statements, Documentation (README, THREATS, PROMPTS).")
    add_bullet("Day 7 (Nov 11-12): ", "Milestone 7 — Cloud Deployment, Demo Accounts, Production End-to-End Verification, Video Recording & Submission.")

    add_h2("Documented & Accepted Limitations")
    add_bullet("Currency Scope: ", "Version one strictly supports Indian Rupee (INR) only. Multi-currency foreign exchange is out of scope.")
    add_bullet("Simulated External Flow: ", "Deposits and withdrawals are simulated cash operations; no external banking gateway is integrated.")
    add_bullet("Full Reversals Only: ", "Version one supports full transaction reversals only; partial reversals are disallowed to prevent accounting ambiguity.")
    add_bullet("Infrastructure Superusers: ", "Database triggers enforce immutability against the application database role. Operating system root and database superusers are outside the application security boundary.")

    output_filename = "LedgerLine_Final_Architecture_Validation.docx"
    doc.save(output_filename)
    print(f"DOCUMENT SUCCESSFULLY GENERATED: {output_filename}")

if __name__ == "__main__":
    build_ledgerline_docx()
