import { useEffect, useState } from 'react';
import { ArrowDownToLine, ArrowUpFromLine, ArrowLeftRight, RefreshCw } from 'lucide-react';
import { fetchAccounts, fetchStatement, deposit, withdraw, transfer, type Account, type StatementItem } from '../lib/ledger';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';

function formatPaise(p: number) {
  return `₹${(p / 100).toFixed(2)}`;
}

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [statement, setStatement] = useState<StatementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modal, setModal] = useState<'deposit' | 'withdraw' | 'transfer' | null>(null);
  const [modalAccountId, setModalAccountId] = useState<string>('');
  const [amount, setAmount] = useState('');
  const [destAccount, setDestAccount] = useState('');
  const [busy, setBusy] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  async function loadAccounts() {
    setLoading(true);
    setError(null);
    try {
      const accs = await fetchAccounts();
      setAccounts(accs);
      if (!selected && accs.length > 0) setSelected(accs[0].id);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  }

  async function loadStatement(accId: string) {
    try {
      const s = await fetchStatement(accId);
      setStatement(s.items ?? []);
    } catch {
      setStatement([]);
    }
  }

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selected) loadStatement(selected);
  }, [selected]);

  function openModal(type: 'deposit' | 'withdraw' | 'transfer', accountId: string) {
    setModal(type);
    setModalAccountId(accountId);
    setAmount('');
    setDestAccount('');
    setModalError(null);
  }

  async function submitModal() {
    setBusy(true);
    setModalError(null);
    const amt = Math.round(parseFloat(amount) * 100);
    if (!amt || amt <= 0) {
      setModalError('Enter a valid amount');
      setBusy(false);
      return;
    }
    const key = crypto.randomUUID();
    try {
      if (modal === 'deposit') await deposit(modalAccountId, amt, key);
      else if (modal === 'withdraw') await withdraw(modalAccountId, amt, key);
      else if (modal === 'transfer') {
        if (!destAccount) {
          setModalError('Enter destination account id');
          setBusy(false);
          return;
        }
        await transfer(modalAccountId, destAccount, amt, key);
      }
      setModal(null);
      await loadAccounts();
      if (selected) await loadStatement(selected);
    } catch (e: any) {
      setModalError(e?.response?.data?.detail ?? 'Operation failed');
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted">
        <span className="animate-spin-slow inline-block w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full mr-2" />
        Loading accounts...
      </div>
    );
  }

  const customerAccounts = accounts.filter((a) => a.account_type === 'CUSTOMER');

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Accounts</h1>
          <p className="text-sm text-muted mt-1">Manage your money and view activity.</p>
        </div>
        <Button variant="secondary" onClick={loadAccounts}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>
      {error && <Alert kind="error">{error}</Alert>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {customerAccounts.map((acc) => (
          <Card key={acc.id} className="p-6 hover:shadow-[var(--shadow-card-hover)] transition-shadow">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-muted">{acc.account_number}</span>
              <Badge tone={acc.status === 'ACTIVE' ? 'success' : 'warning'}>{acc.status}</Badge>
            </div>
            <div className="text-4xl font-bold tracking-tight mb-4 bg-gradient-to-r from-brand-600 to-indigo-400 bg-clip-text text-transparent">
              {formatPaise(acc.projected_balance_paise)}
            </div>
            <div className="flex gap-2">
              <Button onClick={() => openModal('deposit', acc.id)} className="flex-1">
                <ArrowDownToLine className="w-4 h-4" /> Deposit
              </Button>
              <Button variant="secondary" onClick={() => openModal('withdraw', acc.id)} className="flex-1">
                <ArrowUpFromLine className="w-4 h-4" /> Withdraw
              </Button>
              <Button variant="secondary" onClick={() => openModal('transfer', acc.id)} className="flex-1">
                <ArrowLeftRight className="w-4 h-4" /> Transfer
              </Button>
            </div>
          </Card>
        ))}
        {customerAccounts.length === 0 && (
          <Card className="p-6 text-center text-muted">
            No accounts yet. Contact an administrator to get one.
          </Card>
        )}
      </div>

      {customerAccounts.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">Statement</h2>
            <select
              value={selected ?? ''}
              onChange={(e) => setSelected(e.target.value)}
              className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {customerAccounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.account_number}
                </option>
              ))}
            </select>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="py-2 font-medium">Seq</th>
                  <th className="py-2 font-medium">Kind</th>
                  <th className="py-2 font-medium">Type</th>
                  <th className="py-2 font-medium text-right">Amount</th>
                  <th className="py-2 font-medium text-right">Running Balance</th>
                  <th className="py-2 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {statement.map((it) => (
                  <tr key={it.account_activity_sequence} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                    <td className="py-2.5 text-slate-500">{it.account_activity_sequence}</td>
                    <td className="py-2.5">
                      <Badge tone={it.kind === 'POSTING' ? 'info' : 'warning'}>{it.kind}</Badge>
                    </td>
                    <td className="py-2.5">{it.entry_type}</td>
                    <td className="py-2.5 text-right font-medium">{formatPaise(it.amount_paise)}</td>
                    <td className="py-2.5 text-right font-medium">{formatPaise(it.running_balance_paise)}</td>
                    <td className="py-2.5 text-xs text-muted">{new Date(it.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {statement.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted">
                      No activity yet. Make a deposit to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Modal open={modal !== null} onClose={() => setModal(null)} title={modal ? modal.charAt(0).toUpperCase() + modal.slice(1) : ''}>
        <div className="space-y-4">
          {modalError && <Alert kind="error">{modalError}</Alert>}
          <Input
            label="Amount (₹)"
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
          />
          {modal === 'transfer' && (
            <Input
              label="Destination account ID"
              type="text"
              value={destAccount}
              onChange={(e) => setDestAccount(e.target.value)}
              placeholder="paste account UUID"
            />
          )}
          <div className="flex gap-2 pt-2">
            <Button onClick={submitModal} disabled={busy} className="flex-1">
              {busy ? 'Processing...' : 'Confirm'}
            </Button>
            <Button variant="secondary" onClick={() => setModal(null)} disabled={busy} className="flex-1">
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
