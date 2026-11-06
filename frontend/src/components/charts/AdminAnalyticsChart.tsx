import { useMemo } from 'react';
import { ShieldCheck, Landmark } from 'lucide-react';
import type { Account } from '../../lib/ledger';

interface AdminAnalyticsChartProps {
  accounts: Account[];
  reconciliationStatus?: string;
}

export function AdminAnalyticsChart({ accounts, reconciliationStatus = 'ok' }: AdminAnalyticsChartProps) {
  const stats = useMemo(() => {
    let customerTotal = 0;
    let clearingDeposit = 0;
    let clearingWithdrawal = 0;
    let activeCount = 0;
    let frozenCount = 0;

    for (const a of accounts) {
      if (a.account_type === 'CUSTOMER') {
        customerTotal += a.projected_balance_paise;
        if (a.status === 'ACTIVE') activeCount++;
        else frozenCount++;
      } else if (a.account_type === 'SYSTEM_CLEARING_DEPOSIT') {
        clearingDeposit += a.projected_balance_paise;
      } else if (a.account_type === 'SYSTEM_CLEARING_WITHDRAWAL') {
        clearingWithdrawal += a.projected_balance_paise;
      }
    }

    const netClearing = clearingDeposit - clearingWithdrawal;
    const isBalanced = netClearing === customerTotal;

    return {
      customerTotal,
      clearingDeposit,
      clearingWithdrawal,
      netClearing,
      activeCount,
      frozenCount,
      isBalanced,
    };
  }, [accounts]);

  const formatPaise = (p: number) => `₹${(p / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  const maxVal = Math.max(
    10000,
    stats.customerTotal,
    stats.clearingDeposit,
    stats.clearingWithdrawal
  );

  return (
    <div className="bg-slate-900/70 rounded-3xl border border-slate-800/80 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] backdrop-blur-md p-6 text-slate-100">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-7 h-7 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Landmark className="w-4 h-4" />
            </span>
            <h3 className="font-bold text-white text-lg">System Float & Clearing Ledger</h3>
          </div>
          <p className="text-xs text-slate-400">
            Real-time double-entry conservation verification across customer & clearing tiers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
              reconciliationStatus === 'ok'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            {reconciliationStatus === 'ok' ? 'BOOKS BALANCED (1:1)' : 'RECONCILIATION REQUIRED'}
          </span>
        </div>
      </div>

      {/* Visual comparison bars */}
      <div className="space-y-4 mb-6">
        {/* Customer Liabilities */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1.5">
            <span className="font-medium text-slate-300 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500" />
              Customer Platform Liabilities (Credit-Normal)
            </span>
            <span className="font-mono font-bold text-white">{formatPaise(stats.customerTotal)}</span>
          </div>
          <div className="h-3 w-full bg-slate-950/80 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full transition-all duration-700 shadow-xs"
              style={{ width: `${Math.min(100, Math.max(2, (stats.customerTotal / maxVal) * 100))}%` }}
            />
          </div>
        </div>

        {/* Clearing Deposit Assets */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1.5">
            <span className="font-medium text-slate-300 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400" />
              System Clearing Deposit Inflow (Debit-Normal Asset)
            </span>
            <span className="font-mono font-bold text-emerald-300">+{formatPaise(stats.clearingDeposit)}</span>
          </div>
          <div className="h-3 w-full bg-slate-950/80 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-700 shadow-xs"
              style={{ width: `${Math.min(100, Math.max(2, (stats.clearingDeposit / maxVal) * 100))}%` }}
            />
          </div>
        </div>

        {/* Clearing Withdrawal Liabilities */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1.5">
            <span className="font-medium text-slate-300 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-400" />
              System Clearing Withdrawal Outflow (Credit-Normal)
            </span>
            <span className="font-mono font-bold text-rose-300">-{formatPaise(stats.clearingWithdrawal)}</span>
          </div>
          <div className="h-3 w-full bg-slate-950/80 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-rose-500 to-rose-400 rounded-full transition-all duration-700 shadow-xs"
              style={{ width: `${Math.min(100, Math.max(2, (stats.clearingWithdrawal / maxVal) * 100))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Grid summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-800/80 text-xs">
        <div className="p-3 bg-slate-950/70 rounded-2xl border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Net Clearing Float</span>
          <span className="font-mono font-bold text-white text-sm">
            {formatPaise(stats.netClearing)}
          </span>
        </div>
        <div className="p-3 bg-slate-950/70 rounded-2xl border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Customer Balance Total</span>
          <span className="font-mono font-bold text-indigo-400 text-sm">
            {formatPaise(stats.customerTotal)}
          </span>
        </div>
        <div className="p-3 bg-slate-950/70 rounded-2xl border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Active Customers</span>
          <span className="font-mono font-bold text-white text-sm">{stats.activeCount}</span>
        </div>
        <div className="p-3 bg-slate-950/70 rounded-2xl border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Frozen Accounts</span>
          <span className="font-mono font-bold text-white text-sm">{stats.frozenCount}</span>
        </div>
      </div>
    </div>
  );
}
