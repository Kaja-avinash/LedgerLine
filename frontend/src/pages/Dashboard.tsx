import { useEffect, useState } from 'react';
import { ArrowDownToLine, ArrowUpFromLine, ArrowLeftRight, RefreshCw } from 'lucide-react';
import { fetchAccounts, fetchStatement, deposit, withdraw, transfer, type Account, type StatementItem } from '../lib/ledger';

function formatPaise(p: number) {
  return `₹${(p / 100).toFixed(2)}`;
}

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [statement, setStatement] = useState<StatementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // modal state
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
    } catch (e: any) {
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
      if (modal === 'deposit') {
        await deposit(modalAccountId, amt, key);
      } else if (modal === 'withdraw') {
        await withdraw(modalAccountId, amt, key);
      } else if (modal === 'transfer') {
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

  if (loading) return <div className="text-slate-500">Loading accounts...</div>;

  const customerAccounts = accounts.filter((a) => a.account_type === 'CUSTOMER');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Account Holder Dashboard</h1>
        <button
          onClick={loadAccounts}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}

      {/* Account summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {customerAccounts.map((acc) => (
          <div key={acc.id} className="bg-white rounded-lg shadow p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-500">{acc.account_number}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  acc.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                }`}
              >
                {acc.status}
              </span>
            </div>
            <div className="text-3xl font-semibold mb-3">{formatPaise(acc.projected_balance_paise)}</div>
            <div className="flex gap-2">
              <button
                onClick={() => openModal('deposit', acc.id)}
                className="flex-1 flex items-center justify-center gap-1 bg-indigo-600 text-white text-sm py-1.5 rounded hover:bg-indigo-700"
              >
                <ArrowDownToLine className="w-4 h-4" /> Deposit
              </button>
              <button
                onClick={() => openModal('withdraw', acc.id)}
                className="flex-1 flex items-center justify-center gap-1 bg-slate-700 text-white text-sm py-1.5 rounded hover:bg-slate-800"
              >
                <ArrowUpFromLine className="w-4 h-4" /> Withdraw
              </button>
              <button
                onClick={() => openModal('transfer', acc.id)}
                className="flex-1 flex items-center justify-center gap-1 bg-emerald-600 text-white text-sm py-1.5 rounded hover:bg-emerald-700"
              >
                <ArrowLeftRight className="w-4 h-4" /> Transfer
              </button>
            </div>
          </div>
        ))}
        {customerAccounts.length === 0 && (
          <div className="text-slate-500">No accounts yet. Contact an administrator.</div>
        )}
      </div>

      {/* Statement */}
      {customerAccounts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Statement</h2>
            <select
              value={selected ?? ''}
              onChange={(e) => setSelected(e.target.value)}
              className="border border-slate-300 rounded px-2 py-1 text-sm"
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
                <tr className="text-left text-slate-500 border-b">
                  <th className="py-2">Seq</th>
                  <th className="py-2">Kind</th>
                  <th className="py-2">Type</th>
                  <th className="py-2 text-right">Amount</th>
                  <th className="py-2 text-right">Running Balance</th>
                  <th className="py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {statement.map((it) => (
                  <tr key={it.account_activity_sequence} className="border-b last:border-0">
                    <td className="py-2">{it.account_activity_sequence}</td>
                    <td className="py-2">{it.kind}</td>
                    <td className="py-2">{it.entry_type}</td>
                    <td className="py-2 text-right">{formatPaise(it.amount_paise)}</td>
                    <td className="py-2 text-right">{formatPaise(it.running_balance_paise)}</td>
                    <td className="py-2 text-xs text-slate-500">{new Date(it.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {statement.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-slate-500">
                      No activity yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4 capitalize">{modal}</h2>
            {modalError && <div className="mb-3 text-sm text-red-600">{modalError}</div>}
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full border border-slate-300 rounded px-3 py-2"
                />
              </div>
              {modal === 'transfer' && (
                <div>
                  <label className="block text-sm font-medium mb-1">Destination account ID</label>
                  <input
                    type="text"
                    value={destAccount}
                    onChange={(e) => setDestAccount(e.target.value)}
                    className="w-full border border-slate-300 rounded px-3 py-2"
                    placeholder="paste account UUID"
                  />
                </div>
              )}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                onClick={submitModal}
                disabled={busy}
                className="flex-1 bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                {busy ? 'Processing...' : 'Confirm'}
              </button>
              <button
                onClick={() => setModal(null)}
                disabled={busy}
                className="flex-1 bg-slate-200 text-slate-700 py-2 rounded hover:bg-slate-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
