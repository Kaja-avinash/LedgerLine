import { useEffect, useState } from 'react';
import { fetchUsers, fetchAllAccounts, freezeAccount, unfreezeAccount, type AuditUser, type Account } from '../lib/ledger';

function formatPaise(p: number) {
  return `₹${(p / 100).toFixed(2)}`;
}

export default function AdminPanel() {
  const [users, setUsers] = useState<AuditUser[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const [u, a] = await Promise.all([fetchUsers(), fetchAllAccounts()]);
      setUsers(u);
      setAccounts(a);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to load');
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggleFreeze(acc: Account) {
    setBusy(acc.id);
    try {
      if (acc.status === 'ACTIVE') await freezeAccount(acc.id);
      else await unfreezeAccount(acc.id);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Action failed');
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Admin Panel</h1>
      {error && <div className="text-red-600 text-sm">{error}</div>}

      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="font-semibold mb-3">Users ({users.length})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b">
                <th className="py-2">Email</th>
                <th className="py-2">Role</th>
                <th className="py-2">Active</th>
                <th className="py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b last:border-0">
                  <td className="py-2">{u.email}</td>
                  <td className="py-2">{u.role}</td>
                  <td className="py-2">{u.is_active ? 'Yes' : 'No'}</td>
                  <td className="py-2 text-xs text-slate-500">{new Date(u.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="font-semibold mb-3">Accounts ({accounts.length})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b">
                <th className="py-2">Number</th>
                <th className="py-2">Type</th>
                <th className="py-2">Owner</th>
                <th className="py-2 text-right">Balance</th>
                <th className="py-2">Status</th>
                <th className="py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.id} className="border-b last:border-0">
                  <td className="py-2">{a.account_number}</td>
                  <td className="py-2">{a.account_type}</td>
                  <td className="py-2 text-xs text-slate-500">{a.user_id ?? '—'}</td>
                  <td className="py-2 text-right">{formatPaise(a.projected_balance_paise)}</td>
                  <td className="py-2">{a.status}</td>
                  <td className="py-2">
                    {a.account_type === 'CUSTOMER' && (
                      <button
                        onClick={() => toggleFreeze(a)}
                        disabled={busy === a.id}
                        className={`text-xs px-2 py-1 rounded ${
                          a.status === 'ACTIVE'
                            ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                            : 'bg-green-100 text-green-700 hover:bg-green-200'
                        }`}
                      >
                        {a.status === 'ACTIVE' ? 'Freeze' : 'Unfreeze'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
