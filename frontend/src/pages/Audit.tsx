import { useEffect, useState } from 'react';
import { RefreshCw, CheckCircle2, XCircle } from 'lucide-react';
import { fetchReconciliation, fetchClearingBalances } from '../lib/ledger';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';

export default function AuditPage() {
  const [recon, setRecon] = useState<any>(null);
  const [clearing, setClearing] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [r, c] = await Promise.all([fetchReconciliation(), fetchClearingBalances()]);
      setRecon(r);
      setClearing(c);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to load audit data');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted">
        <span className="animate-spin-slow inline-block w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full mr-2" />
        Loading audit data...
      </div>
    );
  }

  const ok = recon?.status === 'ok';

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">System Audit & Reconciliation</h1>
        <Button variant="secondary" onClick={load}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>
      {error && <Alert kind="error">{error}</Alert>}

      {recon && (
        <div
          className={`rounded-2xl border p-6 ${
            ok ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'
          }`}
        >
          <div className="flex items-center gap-2 mb-3">
            {ok ? <CheckCircle2 className="w-6 h-6 text-emerald-600" /> : <XCircle className="w-6 h-6 text-rose-600" />}
            <span className={`text-xl font-semibold ${ok ? 'text-emerald-700' : 'text-rose-700'}`}>
              {ok ? 'Reconciliation OK' : 'Issues Found'}
            </span>
            <Badge tone={ok ? 'success' : 'danger'}>{ok ? 'HEALTHY' : 'ALERT'}</Badge>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-muted">Accounts checked</div>
              <div className="text-lg font-semibold">{recon.accounts_checked}</div>
            </div>
            <div>
              <div className="text-muted">Transactions checked</div>
              <div className="text-lg font-semibold">{recon.transactions_checked}</div>
            </div>
            <div>
              <div className="text-muted">Issue count</div>
              <div className="text-lg font-semibold">{recon.issue_count}</div>
            </div>
            <div>
              <div className="text-muted">Status</div>
              <div className="text-lg font-semibold">{recon.status}</div>
            </div>
          </div>
          {recon.issues?.length > 0 && (
            <ul className="mt-4 space-y-1 text-sm text-rose-700">
              {recon.issues.map((i: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span>•</span>
                  <span>{i}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <Card className="p-6">
        <h2 className="font-semibold text-lg mb-4">System Clearing Balances</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 font-medium">Account ID</th>
                <th className="py-2 font-medium">Type</th>
                <th className="py-2 font-medium text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              {clearing.map((c) => (
                <tr key={c.account_id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="py-2.5 text-xs text-muted font-mono">{c.account_id}</td>
                  <td className="py-2.5">{c.account_type}</td>
                  <td className="py-2.5 text-right font-medium">{(c.balance_paise / 100).toFixed(2)}</td>
                </tr>
              ))}
              {clearing.length === 0 && (
                <tr>
                  <td colSpan={3} className="py-8 text-center text-muted">
                    No clearing accounts.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
