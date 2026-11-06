import { useEffect, useState } from 'react';
import { Shield, RefreshCw } from 'lucide-react';
import { fetchUsers, fetchAllAccounts, freezeAccount, unfreezeAccount, type AuditUser, type Account } from '../lib/ledger';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';

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
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-brand-600" />
          <h1 className="text-2xl font-semibold">Admin Panel</h1>
        </div>
        <Button variant="secondary" onClick={load}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>
      {error && <Alert kind="error">{error}</Alert>}

      <Card className="p-6">
        <h2 className="font-semibold text-lg mb-4">Users <span className="text-muted text-sm font-normal">({users.length})</span></h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 font-medium">Email</th>
                <th className="py-2 font-medium">Role</th>
                <th className="py-2 font-medium">Active</th>
                <th className="py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="py-2.5">{u.email}</td>
                  <td className="py-2.5"><Badge tone="info">{u.role}</Badge></td>
                  <td className="py-2.5">{u.is_active ? 'Yes' : 'No'}</td>
                  <td className="py-2.5 text-xs text-muted">{new Date(u.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="font-semibold text-lg mb-4">Accounts <span className="text-muted text-sm font-normal">({accounts.length})</span></h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 font-medium">Number</th>
                <th className="py-2 font-medium">Type</th>
                <th className="py-2 font-medium">Owner</th>
                <th className="py-2 font-medium text-right">Balance</th>
                <th className="py-2 font-medium">Status</th>
                <th className="py-2 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="py-2.5">{a.account_number}</td>
                  <td className="py-2.5">{a.account_type}</td>
                  <td className="py-2.5 text-xs text-muted">{a.user_id ?? '—'}</td>
                  <td className="py-2.5 text-right font-medium">{formatPaise(a.projected_balance_paise)}</td>
                  <td className="py-2.5">
                    <Badge tone={a.status === 'ACTIVE' ? 'success' : 'warning'}>{a.status}</Badge>
                  </td>
                  <td className="py-2.5">
                    {a.account_type === 'CUSTOMER' && (
                      <Button
                        variant={a.status === 'ACTIVE' ? 'secondary' : 'primary'}
                        onClick={() => toggleFreeze(a)}
                        disabled={busy === a.id}
                        className="text-xs px-2 py-1"
                      >
                        {a.status === 'ACTIVE' ? 'Freeze' : 'Unfreeze'}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
