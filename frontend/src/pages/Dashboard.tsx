import { useEffect, useState, useMemo } from 'react';
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  ArrowLeftRight,
  RefreshCw,
  Copy,
  Check,
  CreditCard,
  Building2,
  Search,
  Sparkles,
  ShieldCheck,
  Info,
  Download,
  Printer,
} from 'lucide-react';
import {
  fetchAccounts,
  fetchStatement,
  deposit,
  withdraw,
  transfer,
  type Account,
  type StatementItem,
} from '../lib/ledger';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { AnimatedCounter } from '../components/ui/AnimatedCounter';
import { BalanceTrendChart, type TimeRangeFilter } from '../components/charts/BalanceTrendChart';
import {
  AccountCardSkeleton,
  ChartSkeleton,
  StatementTableSkeleton,
} from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

function formatPaise(p: number) {
  return `₹${(p / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

export default function Dashboard() {
  const { toast } = useToast();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [statement, setStatement] = useState<StatementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statementLoading, setStatementLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [modal, setModal] = useState<'deposit' | 'withdraw' | 'transfer' | null>(null);
  const [modalAccountId, setModalAccountId] = useState<string>('');
  const [amount, setAmount] = useState('');
  const [destAccount, setDestAccount] = useState('');
  const [busy, setBusy] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Filters for statement table & chart
  const [timeRange, setTimeRange] = useState<TimeRangeFilter>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'ALL' | 'CREDIT' | 'DEBIT' | 'REFUSAL'>('ALL');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  async function loadAccounts(quiet = false) {
    if (!quiet) setLoading(true);
    setError(null);
    try {
      const accs = await fetchAccounts();
      setAccounts(accs);
      if (!selected && accs.length > 0) {
        const cust = accs.find((a) => a.account_type === 'CUSTOMER') || accs[0];
        setSelected(cust.id);
      }
      if (quiet) {
        toast.info('Account balances up to date.', 'Refreshed');
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? 'Failed to load accounts';
      setError(msg);
      toast.error(msg, 'Network Error');
    } finally {
      if (!quiet) setLoading(false);
    }
  }

  async function loadStatement(accId: string) {
    setStatementLoading(true);
    try {
      const s = await fetchStatement(accId);
      setStatement(s.items ?? []);
    } catch {
      setStatement([]);
    } finally {
      setStatementLoading(false);
    }
  }

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selected) loadStatement(selected);
  }, [selected]);

  function copyToClipboard(text: string, label: string) {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    toast.success(`${label} copied to clipboard`, 'Copied');
    setTimeout(() => setCopiedId(null), 2000);
  }

  function openModal(type: 'deposit' | 'withdraw' | 'transfer', accountId: string) {
    setModal(type);
    setModalAccountId(accountId);
    setAmount('');
    setDestAccount('');
    setModalError(null);
  }

  const selectedAccount = useMemo(() => {
    return accounts.find((a) => a.id === selected);
  }, [accounts, selected]);

  const customerAccounts = useMemo(() => {
    return accounts.filter((a) => a.account_type === 'CUSTOMER');
  }, [accounts]);

  // Filtered statement rows considering TimeRange, Operation Type, and Search Query
  const filteredStatement = useMemo(() => {
    const now = Date.now();
    let cutoff = 0;
    if (timeRange === '7D') cutoff = now - 7 * 86400000;
    else if (timeRange === '30D') cutoff = now - 30 * 86400000;
    else if (timeRange === '90D') cutoff = now - 90 * 86400000;

    return statement.filter((item) => {
      // Time range filter
      if (cutoff > 0 && new Date(item.created_at).getTime() < cutoff) {
        return false;
      }

      // Type filter
      if (filterType === 'CREDIT' && item.entry_type !== 'CREDIT') return false;
      if (filterType === 'DEBIT' && item.entry_type !== 'DEBIT') return false;
      if (filterType === 'REFUSAL' && item.kind !== 'REFUSAL') return false;

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const seqMatch = item.account_activity_sequence.toString().includes(q);
        const amountMatch = (item.amount_paise / 100).toString().includes(q);
        const typeMatch = item.entry_type.toLowerCase().includes(q);
        const kindMatch = item.kind.toLowerCase().includes(q);
        const txnMatch = item.transaction_id?.toLowerCase().includes(q) ?? false;
        return seqMatch || amountMatch || typeMatch || kindMatch || txnMatch;
      }
      return true;
    });
  }, [statement, timeRange, filterType, searchQuery]);

  // Export Statement as CSV
  function exportStatementCSV() {
    if (filteredStatement.length === 0) {
      toast.warning('No statement records available in current view to export.', 'Export Empty');
      return;
    }

    const headers = ['Sequence', 'Kind', 'Entry_Type', 'Amount_INR', 'Running_Balance_INR', 'Timestamp', 'Transaction_ID'];
    const rows = filteredStatement.map((it) => [
      it.account_activity_sequence,
      it.kind,
      it.entry_type,
      (it.amount_paise / 100).toFixed(2),
      (it.running_balance_paise / 100).toFixed(2),
      `"${new Date(it.created_at).toISOString()}"`,
      `"${it.transaction_id ?? ''}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const dateStr = new Date().toISOString().split('T')[0];
    const accNum = selectedAccount?.account_number ?? 'Account';
    link.setAttribute('href', url);
    link.setAttribute('download', `LedgerLine_Statement_${accNum}_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success(`Exported ${filteredStatement.length} rows to CSV.`, 'Statement Exported');
  }

  // Print view
  function printStatement() {
    window.print();
  }

  async function submitModal() {
    setBusy(true);
    setModalError(null);
    const amt = Math.round(parseFloat(amount) * 100);
    if (!amt || amt <= 0 || isNaN(amt)) {
      setModalError('Please enter a valid positive amount.');
      setBusy(false);
      return;
    }
    const key = crypto.randomUUID();
    try {
      if (modal === 'deposit') {
        await deposit(modalAccountId, amt, key);
        toast.success(`Successfully deposited ₹${(amt / 100).toFixed(2)}`, 'Deposit Completed');
      } else if (modal === 'withdraw') {
        await withdraw(modalAccountId, amt, key);
        toast.success(`Successfully withdrew ₹${(amt / 100).toFixed(2)}`, 'Withdrawal Completed');
      } else if (modal === 'transfer') {
        if (!destAccount.trim()) {
          setModalError('Destination account UUID is required.');
          setBusy(false);
          return;
        }
        await transfer(modalAccountId, destAccount.trim(), amt, key);
        toast.success(`Successfully transferred ₹${(amt / 100).toFixed(2)}`, 'Transfer Completed');
      }

      setModal(null);
      await loadAccounts(false);
      if (selected) await loadStatement(selected);
    } catch (e: any) {
      const detail = e?.response?.data?.detail ?? 'Transaction could not be completed.';
      setModalError(detail);
      toast.error(detail, 'Transaction Refused');
    } finally {
      setBusy(false);
    }
  }

  const presetAmounts = [500, 1000, 5000, 10000];

  return (
    <div className="space-y-8 animate-fade-in text-slate-100">
      {/* Top Banner / Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Financial Overview
            </h1>
            <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-400 bg-indigo-500/15 border border-indigo-500/30 px-2.5 py-0.5 rounded-full">
              <Sparkles className="w-3 h-3 text-indigo-400" />
              Live Ledger
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time balance projections, cryptographic double-entry postings, and audit statements.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            onClick={() => loadAccounts(true)}
            className="shadow-xs"
          >
            <RefreshCw className="w-4 h-4 text-slate-400" />
            <span>Sync Balances</span>
          </Button>
        </div>
      </div>

      {error && <Alert kind="error" title="Account Retrieval Notice">{error}</Alert>}

      {/* Account Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-indigo-400" />
            <span>Customer Accounts</span>
            <span className="text-xs font-normal text-slate-500">
              ({customerAccounts.length})
            </span>
          </h2>
          {customerAccounts.length > 1 && (
            <span className="text-xs text-slate-400">
              Select an account to view transaction history
            </span>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AccountCardSkeleton />
            <AccountCardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {customerAccounts.map((acc) => {
              const isSelected = selected === acc.id;
              return (
                <div
                  key={acc.id}
                  onClick={() => setSelected(acc.id)}
                  className={`group relative overflow-hidden rounded-3xl p-6 transition-all duration-200 cursor-pointer border ${
                    isSelected
                      ? 'bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 text-white shadow-2xl shadow-indigo-950/60 border-indigo-500/60 ring-2 ring-indigo-500/30'
                      : 'bg-slate-900/70 hover:bg-slate-850/80 text-slate-100 border-slate-800/80 hover:border-slate-700 shadow-md backdrop-blur-md'
                  }`}
                >
                  {/* Subtle Card Background Glow */}
                  <div className="absolute -right-6 -bottom-6 w-36 h-36 rounded-full bg-indigo-500/10 pointer-events-none blur-2xl" />

                  {/* Top Row: Account Number & Status */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-mono font-bold tracking-wider px-2 py-0.5 rounded-lg border ${
                          isSelected
                            ? 'bg-white/10 text-indigo-200 border-white/15'
                            : 'bg-slate-950 text-slate-300 border-slate-800'
                        }`}
                      >
                        {acc.account_number}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(acc.id, 'Account UUID');
                        }}
                        title="Copy Account ID"
                        className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                      >
                        {copiedId === acc.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    <Badge
                      tone={acc.status === 'ACTIVE' ? 'success' : 'warning'}
                      className={isSelected ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : ''}
                    >
                      {acc.status}
                    </Badge>
                  </div>

                  {/* Projected Balance Hero */}
                  <div className="my-5">
                    <span
                      className={`text-xs uppercase tracking-wider block font-semibold mb-1 ${
                        isSelected ? 'text-indigo-300' : 'text-slate-400'
                      }`}
                    >
                      Available Projected Balance
                    </span>
                    <div
                      className={`text-3xl sm:text-4xl font-extrabold tracking-tight font-mono ${
                        isSelected
                          ? 'text-white'
                          : 'bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent'
                      }`}
                    >
                      <AnimatedCounter value={acc.projected_balance_paise} />
                    </div>
                  </div>

                  {/* Micro Meta: Activity Sequence & Currency */}
                  <div
                    className={`flex items-center justify-between text-xs py-2.5 px-3 rounded-xl mb-5 border ${
                      isSelected
                        ? 'bg-white/5 border-white/10 text-slate-300'
                        : 'bg-slate-950/60 border-slate-800 text-slate-400'
                    }`}
                  >
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Seq: <strong className="font-mono text-xs text-white">{acc.last_activity_sequence}</strong></span>
                    </span>
                    <span className="font-semibold text-slate-300">{acc.currency} &bull; Double-Entry</span>
                  </div>

                  {/* Action Buttons */}
                  <div className="grid grid-cols-3 gap-2" onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant={isSelected ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => openModal('deposit', acc.id)}
                      className={isSelected ? 'bg-indigo-600 hover:bg-indigo-500 text-white' : ''}
                    >
                      <ArrowDownToLine className="w-3.5 h-3.5" />
                      <span>Deposit</span>
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openModal('withdraw', acc.id)}
                      className={isSelected ? 'bg-white/10 hover:bg-white/20 text-white border-white/20' : ''}
                    >
                      <ArrowUpFromLine className="w-3.5 h-3.5" />
                      <span>Withdraw</span>
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openModal('transfer', acc.id)}
                      className={isSelected ? 'bg-white/10 hover:bg-white/20 text-white border-white/20' : ''}
                    >
                      <ArrowLeftRight className="w-3.5 h-3.5" />
                      <span>Transfer</span>
                    </Button>
                  </div>
                </div>
              );
            })}

            {customerAccounts.length === 0 && (
              <Card className="p-10 text-center col-span-full border-dashed border-2 border-slate-800">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/15 text-indigo-400 flex items-center justify-center mx-auto mb-3">
                  <Building2 className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-white text-lg mb-1">No Active Customer Accounts</h3>
                <p className="text-sm text-slate-400 max-w-md mx-auto mb-4">
                  Customer accounts are created upon onboarding or via administrator assignment.
                </p>
                <Button variant="secondary" onClick={() => loadAccounts(true)}>
                  Refresh List
                </Button>
              </Card>
            )}
          </div>
        )}
      </div>

      {/* Visual Analytics & Balance Trend Chart */}
      {selectedAccount && (
        <div className="space-y-6">
          {statementLoading ? (
            <ChartSkeleton />
          ) : (
            <BalanceTrendChart
              items={statement}
              currentBalancePaise={selectedAccount.projected_balance_paise}
              accountNumber={selectedAccount.account_number}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
            />
          )}

          {/* Transaction Statement Table Card */}
          <Card className="p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="font-bold text-lg text-white flex items-center gap-2">
                  <span>Ledger Statement & Activity Log</span>
                  <span className="text-xs bg-slate-800 text-slate-300 font-mono px-2 py-0.5 rounded-full border border-slate-700">
                    {filteredStatement.length} items
                  </span>
                  {timeRange !== 'ALL' && (
                    <span className="text-xs text-indigo-400 font-semibold">
                      ({timeRange})
                    </span>
                  )}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Chronological, non-rewritable ledger entries ordered by activity sequence.
                </p>
              </div>

              {/* Utility Tools: Search, Filter, and Export */}
              <div className="flex flex-wrap items-center gap-2.5">
                {/* Search Input */}
                <div className="relative">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="Search seq, amt, or ID..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 text-slate-100 rounded-xl focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition w-44 sm:w-56 placeholder:text-slate-500"
                  />
                </div>

                {/* Filter Pills */}
                <div className="flex items-center rounded-xl bg-slate-950 border border-slate-800 p-1 text-xs">
                  {(['ALL', 'CREDIT', 'DEBIT', 'REFUSAL'] as const).map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => setFilterType(mode)}
                      className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                        filterType === mode
                          ? 'bg-slate-800 text-white shadow-xs'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {mode === 'ALL'
                        ? 'All'
                        : mode === 'CREDIT'
                        ? 'Credits'
                        : mode === 'DEBIT'
                        ? 'Debits'
                        : 'Refused'}
                    </button>
                  ))}
                </div>

                {/* Export Statement CSV Tool */}
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={exportStatementCSV}
                  title="Download CSV Statement"
                  className="px-2.5 py-1.5 text-xs"
                >
                  <Download className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="hidden sm:inline">Export CSV</span>
                </Button>

                {/* Print/Save Document Button */}
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={printStatement}
                  title="Print Statement"
                  className="px-2.5 py-1.5 text-xs"
                >
                  <Printer className="w-3.5 h-3.5 text-slate-400" />
                </Button>
              </div>
            </div>

            {/* Statement Table */}
            {statementLoading ? (
              <StatementTableSkeleton rows={4} />
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-800/80">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 bg-slate-950/70 border-b border-slate-800 text-xs uppercase tracking-wider font-semibold">
                      <th className="py-3 px-4">Seq</th>
                      <th className="py-3 px-4">Classification</th>
                      <th className="py-3 px-4">Operation</th>
                      <th className="py-3 px-4 text-right">Amount</th>
                      <th className="py-3 px-4 text-right">Running Balance</th>
                      <th className="py-3 px-4">Timestamp</th>
                      <th className="py-3 px-4 text-right">Transaction Ref</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredStatement.map((it) => {
                      const isCredit = it.entry_type === 'CREDIT';
                      const isRefusal = it.kind === 'REFUSAL';
                      return (
                        <tr
                          key={it.account_activity_sequence}
                          className="hover:bg-slate-800/40 transition-colors"
                        >
                          {/* Sequence */}
                          <td className="py-3 px-4 font-mono font-semibold text-slate-400 text-xs">
                            #{it.account_activity_sequence}
                          </td>

                          {/* Kind Badge */}
                          <td className="py-3 px-4">
                            <Badge
                              tone={
                                isRefusal
                                  ? 'danger'
                                  : it.kind === 'POSTING'
                                  ? 'info'
                                  : 'neutral'
                              }
                            >
                              {it.kind}
                            </Badge>
                          </td>

                          {/* Operation Entry Type */}
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md ${
                                isCredit
                                  ? 'text-emerald-300 bg-emerald-500/15 border border-emerald-500/25'
                                  : isRefusal
                                  ? 'text-rose-300 bg-rose-500/15 border border-rose-500/25'
                                  : 'text-amber-300 bg-amber-500/15 border border-amber-500/25'
                              }`}
                            >
                              {isCredit ? (
                                <ArrowDownToLine className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <ArrowUpFromLine className="w-3 h-3 text-amber-400" />
                              )}
                              {it.entry_type}
                            </span>
                          </td>

                          {/* Amount */}
                          <td className="py-3 px-4 text-right font-mono font-bold text-xs">
                            <span
                              className={
                                isCredit
                                  ? 'text-emerald-400'
                                  : isRefusal
                                  ? 'text-slate-500 line-through'
                                  : 'text-slate-200'
                              }
                            >
                              {isCredit ? '+' : '-'}
                              {formatPaise(it.amount_paise)}
                            </span>
                          </td>

                          {/* Running Balance */}
                          <td className="py-3 px-4 text-right font-mono font-semibold text-xs text-white">
                            {formatPaise(it.running_balance_paise)}
                          </td>

                          {/* Timestamp */}
                          <td className="py-3 px-4 text-xs text-slate-400">
                            {new Date(it.created_at).toLocaleString('en-IN', {
                              dateStyle: 'medium',
                              timeStyle: 'short',
                            })}
                          </td>

                          {/* Ref ID */}
                          <td className="py-3 px-4 text-right text-xs">
                            {it.transaction_id ? (
                              <button
                                type="button"
                                onClick={() => copyToClipboard(it.transaction_id!, 'Transaction ID')}
                                title={it.transaction_id}
                                className="font-mono text-indigo-400 hover:text-indigo-300 hover:underline flex items-center gap-1 ml-auto cursor-pointer"
                              >
                                <span>{it.transaction_id.slice(0, 8)}...</span>
                                <Copy className="w-3 h-3 text-slate-500" />
                              </button>
                            ) : (
                              <span className="text-slate-500">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}

                    {filteredStatement.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-12 text-center text-slate-400">
                          <Info className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                          <p className="font-medium text-slate-300">No matching activity found</p>
                          <p className="text-xs text-slate-500 mt-1">
                            {searchQuery || timeRange !== 'ALL'
                              ? 'Try clearing the search query or resetting the time-range filter'
                              : 'Execute a deposit to record the first double-entry ledger posting'}
                          </p>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Transaction Modal (Deposit / Withdraw / Transfer) */}
      <Modal
        open={modal !== null}
        onClose={() => setModal(null)}
        title={
          modal === 'deposit'
            ? 'Deposit Funds'
            : modal === 'withdraw'
            ? 'Withdraw Funds'
            : 'Transfer to Account'
        }
        subtitle={
          modal === 'deposit'
            ? 'Credit customer account via Deposit Clearing (INR)'
            : modal === 'withdraw'
            ? 'Debit customer account via Withdrawal Clearing (INR)'
            : 'Atomically move funds between accounts'
        }
      >
        <div className="space-y-5">
          {modalError && <Alert kind="error" title="Transaction Error">{modalError}</Alert>}

          {/* Quick preset chips */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Preset Amount (INR)
            </label>
            <div className="grid grid-cols-4 gap-2">
              {presetAmounts.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setAmount(p.toString())}
                  className={`py-1.5 text-xs font-semibold rounded-xl border transition cursor-pointer ${
                    amount === p.toString()
                      ? 'bg-indigo-600/25 border-indigo-500 text-indigo-300 shadow-xs'
                      : 'bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800/80 hover:text-white'
                  }`}
                >
                  ₹{p.toLocaleString()}
                </button>
              ))}
            </div>
          </div>

          {/* Amount input */}
          <Input
            label="Amount (₹)"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="e.g. 500.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
          />

          {/* Destination Account for transfers */}
          {modal === 'transfer' && (
            <Input
              label="Destination Account ID (UUID)"
              type="text"
              value={destAccount}
              onChange={(e) => setDestAccount(e.target.value)}
              placeholder="e.g. 3d580fd7-..."
              helperText="Paste the target account UUID from the admin panel or user dashboard"
            />
          )}

          {/* Projected Balance Preview */}
          {amount && !isNaN(parseFloat(amount)) && parseFloat(amount) > 0 && selectedAccount && (
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between text-slate-400">
                <span>Current Balance:</span>
                <span className="font-mono text-slate-200">{formatPaise(selectedAccount.projected_balance_paise)}</span>
              </div>
              <div className="flex justify-between font-semibold text-slate-100">
                <span>Projected New Balance:</span>
                <span className="font-mono text-indigo-400">
                  {formatPaise(
                    modal === 'deposit'
                      ? selectedAccount.projected_balance_paise + Math.round(parseFloat(amount) * 100)
                      : selectedAccount.projected_balance_paise - Math.round(parseFloat(amount) * 100)
                  )}
                </span>
              </div>
            </div>
          )}

          {/* Modal Actions */}
          <div className="flex gap-2.5 pt-2">
            <Button
              onClick={submitModal}
              loading={busy}
              className="flex-1"
              variant={modal === 'deposit' ? 'success' : modal === 'withdraw' ? 'danger' : 'primary'}
            >
              {modal === 'deposit' ? 'Confirm Deposit' : modal === 'withdraw' ? 'Confirm Withdrawal' : 'Confirm Transfer'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setModal(null)}
              disabled={busy}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
