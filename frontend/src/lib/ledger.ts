import { api } from './api';

export interface Account {
  id: string;
  account_number: string;
  user_id: string | null;
  account_type: string;
  currency: string;
  status: string;
  projected_balance_paise: number;
  last_activity_sequence: number;
  created_at: string;
}

export interface StatementItem {
  kind: string;
  entry_type: string;
  amount_paise: number;
  running_balance_paise: number;
  account_activity_sequence: number;
  created_at: string;
  transaction_id: string | null;
}

export interface Statement {
  account_id: string;
  account_number: string;
  projected_balance_paise: number;
  items: StatementItem[];
}

export interface AuditUser {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export async function fetchUsers(): Promise<AuditUser[]> {
  const res = await api.get('/api/users');
  return res.data;
}

export async function fetchAllAccounts(): Promise<Account[]> {
  const res = await api.get('/api/accounts');
  return res.data;
}

export async function fetchReconciliation() {
  const res = await api.get('/api/audit/reconciliation');
  return res.data as { status: string; issue_count: number; issues: string[]; accounts_checked: number; transactions_checked: number };
}

export async function fetchClearingBalances() {
  const res = await api.get('/api/audit/clearing-balances');
  return res.data as { account_id: string; account_type: string; balance_paise: number }[];
}

export async function freezeAccount(accountId: string) {
  const res = await api.post(`/api/accounts/${accountId}/freeze`);
  return res.data;
}

export async function unfreezeAccount(accountId: string) {
  const res = await api.post(`/api/accounts/${accountId}/unfreeze`);
  return res.data;
}

export async function fetchAccounts(): Promise<Account[]> {
  const res = await api.get('/api/accounts');
  return res.data;
}

export async function fetchStatement(accountId: string): Promise<Statement> {
  const res = await api.get(`/api/accounts/${accountId}/statement`);
  return res.data;
}

export async function deposit(accountId: string, amountPaise: number, key: string) {
  const res = await api.post(
    '/api/transactions/deposit',
    { account_id: accountId, amount_paise: amountPaise },
    { headers: { 'Idempotency-Key': key } },
  );
  return res.data;
}

export async function withdraw(accountId: string, amountPaise: number, key: string) {
  const res = await api.post(
    '/api/transactions/withdraw',
    { account_id: accountId, amount_paise: amountPaise },
    { headers: { 'Idempotency-Key': key } },
  );
  return res.data;
}

export async function transfer(fromId: string, toId: string, amountPaise: number, key: string) {
  const res = await api.post(
    '/api/transactions/transfer',
    { from_account_id: fromId, to_account_id: toId, amount_paise: amountPaise },
    { headers: { 'Idempotency-Key': key } },
  );
  return res.data;
}
