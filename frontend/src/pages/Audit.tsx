import { useEffect, useState } from 'react';
import { fetchReconciliation, fetchClearingBalances } from '../lib/ledger';

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

  if (loading) return <div className="text-slate-500">Loading audit data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">System Audit & Reconciliation</h1>
        <button onClick={load} className="text-sm text-indigo-600 hover:underline">
          Refresh
        </button>
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}

      {recon && (
        <div
          className={`rounded-lg shadow p-5 ${
            recon.status === 'ok' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-lg font-semibold ${recon.status === 'ok' ? 'text-green-700' : 'text-red-700'}`}>
              {recon.status === 'ok' ? '✓ Reconciliation OK' : '✗ Issues Found'}
            </span>
          </div>
          <div className="text-sm text-slate-700 space-y-1">
            <div>Accounts checked: {recon.accounts_checked}</div>
            <div>Transactions checked: {recon.transactions_checked}</div>
            <div>Issue count: {recon.issue_count}</div>
          </div>
          {recon.issues?.length > 0 && (
            <ul className="mt-3 text-sm text-red-700 list-disc list-inside">
              {recon.issues.map((i: string, idx: number) => (
                <li key={idx}>{i}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="font-semibold mb-3">System Clearing Balances</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b">
              <th className="py-2">Account ID</th>
              <th className="py-2">Type</th>
              <th className="py-2 text-right">Balance (paise)</th>
            </tr>
          </thead>
          <tbody>
            {clearing.map((c) => (
              <tr key={c.account_id} className="border-b last:border-0">
                <td className="py-2 text-xs text-slate-500">{c.account_id}</td>
                <td className="py-2">{c.account_type}</td>
                <td className="py-2 text-right">{(c.balance_paise / 100).toFixed(2)}</td>
              </tr>
            ))}
            {clearing.length === 0 && (
              <tr>
                <td colSpan={3} className="py-4 text-center text-slate-500">
                  No clearing accounts.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
