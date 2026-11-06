import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs('temp_diagrams', exist_ok=True)

def draw_box(ax, x, y, w, h, text, title="", bg="#F0F4F8", border="#102C57", text_color="#102C57", fontsize=8.5, title_fontsize=9.5, boxstyle="round,pad=0.25"):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle=boxstyle, linewidth=1.5, edgecolor=border, facecolor=bg)
    ax.add_patch(rect)
    if title:
        ax.text(x + w/2, y + h - 0.22, title, ha='center', va='center', fontsize=title_fontsize, weight='bold', color=border)
        ax.text(x + w/2, y + (h - 0.3)/2, text, ha='center', va='center', fontsize=fontsize, color=text_color)
    else:
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=fontsize, weight='bold' if not title else 'normal', color=text_color)

def draw_arrow(ax, x1, y1, x2, y2, label="", color="#102C57", label_offset=(0, 0.15), fontsize=8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5, mutation_scale=12))
    if label:
        mx = (x1 + x2)/2 + label_offset[0]
        my = (y1 + y2)/2 + label_offset[1]
        ax.text(mx, my, label, ha='center', va='center', fontsize=fontsize, color=color, weight='bold',
                bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85))

# ==============================================================================
# Diagram 1: Overall System Architecture
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6.5), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis('off')

ax.text(5.5, 6.2, "LedgerLine — Final Technology & System Architecture", ha='center', va='center', fontsize=14, weight='bold', color="#102C57")
ax.text(5.5, 5.85, "Layered Architecture with Atomic Idempotency, Row Locks & Deferred Constraint Triggers", ha='center', va='center', fontsize=9.5, style='italic', color="#555555")

draw_box(ax, 0.4, 4.2, 2.8, 1.3, "React 18 + TypeScript + Vite\nTailwind CSS\nDeterministic UUIDv4 Idempotency Key", "Presentation Layer", bg="#EBF4FF", border="#2B6CB0")
draw_box(ax, 3.8, 4.2, 3.2, 1.3, "FastAPI Routers (/auth, /accounts, /operations)\nPydantic v2 Minor Unit (Paise) Validation\nJWT Authentication & Token Revocation", "Transport Layer (FastAPI)", bg="#E6FFFA", border="#2C7A7B")
draw_box(ax, 7.6, 4.2, 3.0, 1.3, "Early Atomic Idempotency Claimer\nDeterministic Global Lock Coordinator\nDouble-Entry Ledger Engine\nMulti-Account Reconciliation Engine", "Core Financial Domain", bg="#FEFCBF", border="#B7791F")

draw_box(ax, 0.4, 0.4, 10.2, 3.3, "", "PostgreSQL 15+ ACID Database Engine", bg="#F7FAFC", border="#102C57")

draw_box(ax, 0.7, 1.8, 2.9, 1.3, "READ COMMITTED Isolation\nSELECT ... FOR UPDATE\nSorted Account Lock Ordering\nParent-Row Header Locking", "Concurrency & Locking", bg="#EDF2F7", border="#4A5568")
draw_box(ax, 4.0, 1.8, 3.1, 1.3, "Scoped Customer Non-Negative Check\nCurrency INR CHECK Constraint\nuq_single_transaction_reversal\nuq_account_activity_sequence", "Relational Constraints", bg="#EDF2F7", border="#4A5568")
draw_box(ax, 7.5, 1.8, 2.8, 1.3, "Deferred Transaction Closure\nDeferred Idempotency Terminal Check\nParent Row Lock on Ledger Insert", "Deferred Constraint Triggers", bg="#EDF2F7", border="#4A5568")

draw_box(ax, 0.7, 0.7, 9.6, 0.85, "BEFORE UPDATE / DELETE Triggers on financial_transactions, ledger_entries,\naccount_activity_events, refused_operations, admin_audit_events, security_audit_events", "Immutability & Audit Boundary", bg="#FED7D7", border="#C53030")

draw_arrow(ax, 3.2, 4.85, 3.8, 4.85, "HTTPS / JSON")
draw_arrow(ax, 7.0, 4.85, 7.6, 4.85, "Service Call")
draw_arrow(ax, 9.1, 4.2, 9.1, 3.7, "SQLAlchemy 2.0")

plt.savefig('temp_diagrams/diagram_1_overall_architecture.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 2: Component Boundaries & Actors
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(5.5, 5.7, "LedgerLine — Actor Boundaries & Component Relationships", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

draw_box(ax, 0.5, 4.2, 2.8, 1.0, "Administrator\n(Account Mgmt, Audited Reversals)", bg="#E2E8F0", border="#2D3748")
draw_box(ax, 4.1, 4.2, 2.8, 1.0, "Account Holder\n(Simulated Deposit, Withdraw, Transfer)", bg="#E2E8F0", border="#2D3748")
draw_box(ax, 7.7, 4.2, 2.8, 1.0, "Auditor\n(Read-Only Statements, Ledger & Audit Logs)", bg="#E2E8F0", border="#2D3748")

draw_box(ax, 0.5, 2.6, 10.0, 1.1, "JWT Authenticator -> Token Revocation Check -> RBAC Role Guard -> BOLA Ownership Guard", "API Gateway & Security Boundary", bg="#EBF8FF", border="#3182CE")

draw_box(ax, 0.5, 0.5, 2.2, 1.6, "users\naccounts\nrevoked_tokens", "Identity & Accounts", bg="#FAF5FF", border="#6B46C1")
draw_box(ax, 3.0, 0.5, 2.5, 1.6, "financial_transactions\nledger_entries\naccount_activity_events", "Immutable Ledger", bg="#F0FFF4", border="#2F855A")
draw_box(ax, 5.8, 0.5, 2.3, 1.6, "idempotency_records", "Deduplication & Cache", bg="#FFFAF0", border="#DD6B20")
draw_box(ax, 8.4, 0.5, 2.1, 1.6, "refused_operations\nadmin_audit_events\nsecurity_audit_events", "Separated Audit", bg="#FFF5F5", border="#E53E3E")

draw_arrow(ax, 1.9, 4.2, 3.0, 3.7)
draw_arrow(ax, 5.5, 4.2, 5.5, 3.7)
draw_arrow(ax, 9.1, 4.2, 8.0, 3.7)

draw_arrow(ax, 2.5, 2.6, 1.6, 2.1)
draw_arrow(ax, 4.5, 2.6, 4.3, 2.1)
draw_arrow(ax, 6.5, 2.6, 7.0, 2.1)
draw_arrow(ax, 8.5, 2.6, 9.5, 2.1)

plt.savefig('temp_diagrams/diagram_2_component_boundaries.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 3: Double-Entry Accounting Operations
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6.5), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis('off')

ax.text(5.5, 6.2, "Double-Entry Postings Across Financial Operations", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")
ax.text(5.5, 5.85, "Every Transaction Balances: Sum(Debits) == Sum(Credits)", ha='center', va='center', fontsize=9.5, style='italic', color="#555555")

draw_box(ax, 0.5, 3.8, 4.8, 1.7, "DEBIT: SYSTEM_CLEARING_DEPOSIT (Asset increases)\nCREDIT: Customer Account A (Liability increases +1,000)\nNet Customer Impact: +Rs 1,000 | Invariant Conserved", "1. Simulated External Deposit (e.g. Rs 1,000)", bg="#E6FFFA", border="#234E52")
draw_box(ax, 5.7, 3.8, 4.8, 1.7, "DEBIT: Customer Account A (Liability decreases -400)\nCREDIT: SYSTEM_CLEARING_WITHDRAWAL (Settlement increases)\nNet Customer Impact: -Rs 400 | Invariant Conserved", "2. Simulated External Withdrawal (e.g. Rs 400)", bg="#FEFCBF", border="#744210")
draw_box(ax, 0.5, 1.5, 4.8, 1.8, "DEBIT: Source Customer Account A (-Rs 300)\nCREDIT: Destination Customer Account B (+Rs 300)\nNet Customer Impact: Exactly Rs 0 (Conserved)", "3. Internal Account Transfer (e.g. Rs 300)", bg="#EBF8FF", border="#2B6CB0")
draw_box(ax, 5.7, 1.5, 4.8, 1.8, "DEBIT: Destination Customer Account B (-Rs 300)\nCREDIT: Source Customer Account A (+Rs 300)\nValidates Account B has >= Rs 300 before debiting!", "4. Full Compensating Reversal (of Transfer Rs 300)", bg="#FED7D7", border="#9B2C2C")

plt.savefig('temp_diagrams/diagram_3_double_entry_operations.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 4: Transaction Execution Sequence
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 7), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7)
ax.axis('off')

ax.text(5.5, 6.7, "Exact Financial Transaction Execution Sequence", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

steps = [
    "1. Client sends POST /transfers (Idempotency-Key, from_id, to_id, amount_paise)",
    "2. Security Guard verifies JWT token, checks revoked_tokens table, verifies ownership of from_id",
    "3. BEGIN PostgreSQL Transaction (READ COMMITTED isolation)",
    "4. Early Atomic Idempotency Claim: INSERT INTO idempotency_records ... ON CONFLICT DO NOTHING",
    "   -> If claim returns 0 rows: Query committed record -> Return cached response (Idempotent-Replay: true)",
    "   -> If claim succeeds: Transaction owns the key. Proceed with execution.",
    "5. Acquire Deterministic Row Locks: SELECT ... FROM accounts WHERE id IN (low_id, high_id) FOR UPDATE",
    "6. Check Business Constraints: Source active? Dest active? Balance >= amount? Currency == INR?",
    "   -> If Insufficient Funds: Record refused_operations, update idempotency status='REFUSED', COMMIT",
    "7. Insert unclosed financial_transactions header (is_closed = FALSE)",
    "8. Insert balanced ledger_entries (Debit from_id, Credit to_id, allocate account_activity_sequence)",
    "9. Transition header: UPDATE financial_transactions SET is_closed = TRUE, posted_at = NOW()",
    "10. Finalize idempotency: UPDATE idempotency_records SET status = 'COMPLETED', code = 200, body = result",
    "11. COMMIT Transaction: Deferred triggers execute (verify_financial_transaction_closure & verify_idempotency)",
    "12. Return HTTP 200 OK with transaction receipt"
]

y_pos = 6.0
for step in steps:
    is_sub = step.startswith("   ->")
    color = "#2D3748" if not is_sub else "#C53030"
    ax.text(0.8 if not is_sub else 1.3, y_pos, step, fontsize=8.5, weight="bold" if not is_sub else "normal", color=color)
    y_pos -= 0.39

plt.savefig('temp_diagrams/diagram_4_transaction_sequence.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 5: Concurrent Idempotency Execution
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(5.5, 5.7, "Concurrent Idempotency Key Claiming under PostgreSQL READ COMMITTED", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

draw_box(ax, 0.5, 4.0, 4.5, 1.2, "BEGIN Tx 1;\nINSERT INTO idempotency_records (status='IN_PROGRESS')\n-> Successfully claims key row under row-level lock", "Worker 1 (Wins Claim)", bg="#E6FFFA", border="#234E52")
draw_box(ax, 6.0, 4.0, 4.5, 1.2, "BEGIN Tx 2;\nINSERT INTO idempotency_records (status='IN_PROGRESS')\n-> Hits Unique Constraint on (user_id, key)! BLOCKS waiting for Tx 1", "Worker 2 (Concurrent Replay)", bg="#FEFCBF", border="#744210")

draw_box(ax, 0.5, 1.8, 4.5, 1.6, "1. Acquires Account Locks FOR UPDATE\n2. Verifies Balances & Inserts Postings\n3. Updates idempotency status='COMPLETED'\n4. COMMIT Transaction (Key committed)", "Tx 1 Financial Execution", bg="#EBF8FF", border="#2B6CB0")

draw_box(ax, 6.0, 1.8, 4.5, 1.6, "1. Tx 1 commits -> Tx 2 unblocks immediately!\n2. ON CONFLICT DO NOTHING returns 0 rows\n3. Tx 2 queries committed record\n4. Hashes match -> Returns cached response (HTTP 200)", "Tx 2 Resolution (Zero Mutations)", bg="#F0FFF4", border="#276749")

draw_arrow(ax, 2.75, 4.0, 2.75, 3.4)
draw_arrow(ax, 8.25, 4.0, 8.25, 3.4)
draw_arrow(ax, 5.0, 2.6, 6.0, 2.6, "Tx 1 Commits")

draw_box(ax, 0.5, 0.4, 10.0, 0.9, "If Tx 1 Aborts: Tx 2 unblocks, ON CONFLICT DO NOTHING inserts successfully, and Tx 2 becomes primary executor!", "Crash Recovery Guarantee", bg="#EDF2F7", border="#4A5568")

plt.savefig('temp_diagrams/diagram_5_concurrent_idempotency.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 6: Defense-in-Depth Authorization
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(5.5, 5.7, "Defense-in-Depth Authorization & Security Layers", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

draw_box(ax, 0.5, 4.2, 10.0, 1.0, "Verify cryptographic signature, check expiration (exp), check revoked_tokens table for jti revocation.\nVerify user.is_active == TRUE. Reject invalid credentials with HTTP 401.", "Layer 1: Transport & JWT Authentication", bg="#EBF8FF", border="#2B6CB0")
draw_box(ax, 0.5, 2.9, 10.0, 1.0, "Verify caller role (ADMINISTRATOR, ACCOUNT_HOLDER, AUDITOR).\nEnforce that Admins cannot withdraw customer funds; Auditors have zero write access. Reject with HTTP 403.", "Layer 2: Role-Based Access Control (RBAC)", bg="#E6FFFA", border="#2C7A7B")
draw_box(ax, 0.5, 1.6, 10.0, 1.0, "Verify caller owns the debited account ID (account.user_id == current_user.id).\nReject identifier manipulation and BOLA/IDOR attacks with HTTP 403; log security_audit_events.", "Layer 3: Resource Ownership Guard (BOLA/IDOR)", bg="#FEFCBF", border="#B7791F")
draw_box(ax, 0.5, 0.3, 10.0, 1.0, "Re-verify account ownership and status == 'ACTIVE' on the locked database row inside the transaction.\nVerify non-negative balance, currency == 'INR', and non-self-transfer. Reject business failures with HTTP 400.", "Layer 4: Deep Financial Service Authorization", bg="#FED7D7", border="#C53030")

plt.savefig('temp_diagrams/diagram_6_defense_in_depth.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 7: Reversal Validation Flowchart
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6.5), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.5)
ax.axis('off')

ax.text(5.5, 6.2, "Reversal Validation & Compensating Postings Workflow", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

draw_box(ax, 0.5, 4.7, 3.2, 1.1, "Admin submits POST /operations/reverse\n(target_tx_id, reason_narrative)\nRequires Idempotency-Key", "1. Reversal Request", bg="#E2E8F0", border="#4A5568")
draw_box(ax, 4.2, 4.7, 3.2, 1.1, "1. Is target_tx a reversal? (reverses_tx IS NULL)\n2. Has it already been reversed? (uq constraint)\nIf invalid -> Reject with HTTP 422 or 409", "2. Reversal Legality Check", bg="#FEFCBF", border="#B7791F")
draw_box(ax, 7.8, 4.7, 2.7, 1.1, "Acquire row locks on all original accounts\nin ascending UUID order\nSELECT ... FOR UPDATE", "3. Deterministic Locking", bg="#EBF8FF", border="#2B6CB0")

draw_box(ax, 0.5, 2.2, 4.8, 1.7, "Check EVERY customer account debited by reversal:\n- Deposit reversal: Debits customer recipient account\n- Transfer reversal: Debits original destination account\nVerify account.projected_balance >= debit amount.\nIf balance insufficient -> Reject HTTP 400 (No overdrafts!)", "4. Balance Sufficiency on ALL Debited Customer Accounts", bg="#FED7D7", border="#C53030")

draw_box(ax, 5.7, 2.2, 4.8, 1.7, "Create new transaction (type='REVERSAL', is_closed=FALSE)\nInsert exact inverted postings (Debit <-> Credit, identical amounts)\nUpdate header is_closed = TRUE\nCommit & Log admin_audit_events", "5. Compensating Postings & Commit", bg="#F0FFF4", border="#22543D")

draw_arrow(ax, 3.7, 5.25, 4.2, 5.25)
draw_arrow(ax, 7.4, 5.25, 7.8, 5.25)
draw_arrow(ax, 9.1, 4.7, 9.1, 3.9)
draw_arrow(ax, 9.1, 3.9, 2.9, 3.9)
draw_arrow(ax, 5.3, 3.0, 5.7, 3.0)

plt.savefig('temp_diagrams/diagram_7_reversal_validation.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 8: 4-Way Reconciliation Process
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 6), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
ax.axis('off')

ax.text(5.5, 5.7, "Multi-Account 4-Way Reconciliation Process", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

draw_box(ax, 0.5, 3.8, 4.8, 1.3, "Customer Accounts (Liability):\nCredits - Debits == projected_balance_paise?\nValidates zero balance drift for every account.", "1. Customer Liability Reconciliation", bg="#EBF8FF", border="#2B6CB0")
draw_box(ax, 5.7, 3.8, 4.8, 1.3, "Deposit Clearing Account (Asset):\nDebits - Credits == projected_balance_paise?\nValidates net external cash injected after reversals.", "2. Deposit Clearing Reconciliation", bg="#E6FFFA", border="#234E52")
draw_box(ax, 0.5, 1.8, 4.8, 1.3, "Withdrawal Clearing Account (Liability):\nCredits - Debits == projected_balance_paise?\nValidates net external cash disbursed after reversals.", "3. Withdrawal Clearing Reconciliation", bg="#FEFCBF", border="#744210")
draw_box(ax, 5.7, 1.8, 4.8, 1.3, "Double-Entry Balance: Sum(Debits) == Sum(Credits) for all Tx?\nConservation: Closing == Opening + Net Deposits - Net Withdrawals?\nZero discrepancy check across entire database.", "4. Platform Invariant Verification", bg="#FAF5FF", border="#553C9A")

draw_box(ax, 1.5, 0.4, 8.0, 0.9, "Outputs structured immutable JSON report accessible to Administrators and Auditors.\nDoes not alter historical database state.", "Reconciliation Report Output", bg="#EDF2F7", border="#4A5568")

plt.savefig('temp_diagrams/diagram_8_reconciliation_process.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# Diagram 9: Database Entity-Relationship Diagram
# ==============================================================================
fig, ax = plt.subplots(figsize=(11, 7.5), dpi=200)
ax.set_xlim(0, 11)
ax.set_ylim(0, 7.5)
ax.axis('off')

ax.text(5.5, 7.2, "LedgerLine — Final Relational Database Schema (ER Diagram)", ha='center', va='center', fontsize=13, weight='bold', color="#102C57")

draw_box(ax, 0.4, 5.1, 2.8, 1.8, "id (UUID PK)\nemail (VARCHAR UNIQUE)\nhashed_password (VARCHAR)\nrole (CHECK: ADMIN/HOLDER/AUDITOR)\nis_active (BOOLEAN)\ncreated_at / updated_at", "users", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 3.9, 5.1, 3.2, 1.8, "id (UUID PK)\naccount_number (UNIQUE)\nuser_id (UUID FK -> users)\naccount_type (CHECK: CUSTOMER/CLEARING)\nstatus (CHECK: ACTIVE/FROZEN/CLOSED)\ncurrency (CHECK: 'INR')\nprojected_balance_paise (BIGINT)\nlast_activity_sequence (BIGINT)", "accounts", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 7.8, 5.1, 2.8, 1.8, "id (UUID PK)\ntransaction_type (CHECK: DEP/WTH/TRF/REV)\ninitiator_user_id (UUID FK)\nreference_id (VARCHAR UNIQUE)\nis_closed (BOOLEAN)\nreverses_transaction_id (FK, UNIQUE)\nposted_at (TIMESTAMP)", "financial_transactions", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 3.9, 2.7, 3.2, 2.1, "id (UUID PK)\ntransaction_id (UUID FK)\naccount_id (UUID FK)\nactivity_event_id (UUID FK)\nentry_type (CHECK: DEBIT/CREDIT)\namount_paise (BIGINT > 0)\nrunning_balance_paise (BIGINT)\ncreated_at (TIMESTAMP)", "ledger_entries", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 0.4, 2.7, 2.8, 2.1, "user_id (UUID PK, FK)\nkey (VARCHAR PK)\nrequest_path / method / hash\nstatus (CHECK: IN_PROGRESS/COMPL/REF)\nresponse_status_code (INT)\nresponse_body (JSONB)\ntransaction_id (UUID FK)", "idempotency_records", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 7.8, 2.7, 2.8, 2.1, "id (UUID PK)\nuser_id (UUID FK)\naccount_id (UUID FK)\nactivity_event_id (UUID FK)\nobserved_balance_paise (BIGINT)\nattempted_amount_paise (BIGINT)\nreason_code / reason_message", "refused_operations", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 0.4, 0.4, 3.1, 1.9, "id (UUID PK)\naccount_id (UUID FK -> accounts)\nactivity_sequence (BIGINT)\nevent_type ('POSTING' / 'REFUSAL')\ncreated_at (TIMESTAMP)\nUQ(account_id, activity_sequence)", "account_activity_events", bg="#F0FFF4", border="#276749")

draw_box(ax, 4.0, 0.4, 3.0, 1.9, "token_jti (VARCHAR UNIQUE PK)\nuser_id (UUID FK -> users)\nexpires_at / revoked_at\nreason (LOGOUT / ...)", "revoked_tokens", bg="#F7FAFC", border="#2D3748")

draw_box(ax, 7.5, 0.4, 3.2, 1.9, "admin_audit_events\n(admin_user_id, action, narrative)\nsecurity_audit_events\n(actor_user_id, ip, bola_event)", "Audit & Security Logs", bg="#FFF5F5", border="#E53E3E")

draw_arrow(ax, 3.2, 6.0, 3.9, 6.0, "1:N")
draw_arrow(ax, 5.5, 5.1, 5.5, 4.8, "1:N")
draw_arrow(ax, 7.8, 6.0, 7.1, 6.0, "initiates")
draw_arrow(ax, 8.5, 5.1, 7.1, 3.7, "1:N")
draw_arrow(ax, 1.8, 5.1, 1.8, 4.8, "scopes")
draw_arrow(ax, 3.9, 4.0, 3.5, 1.5, "FK")
draw_arrow(ax, 7.8, 4.0, 3.5, 1.5, "FK")

plt.savefig('temp_diagrams/diagram_9_er_diagram.png', bbox_inches='tight')
plt.close()
print("All 9 diagrams re-rendered successfully!")
