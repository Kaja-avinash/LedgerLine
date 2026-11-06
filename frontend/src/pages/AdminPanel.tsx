import { useEffect, useState, useMemo } from 'react';
import {
  Shield,
  RefreshCw,
  Users,
  CreditCard,
  Lock,
  Unlock,
  Copy,
  Check,
  Search,
  CheckCircle2,
  UserCheck,
  AlertTriangle,
} from 'lucide-react';
import {
  fetchUsers,
  fetchAllAccounts,
  freezeAccount,
  unfreezeAccount,
  type AuditUser,
  type Account,
} from '../lib/ledger';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { AdminAnalyticsChart } from '../components/charts/AdminAnalyticsChart';
import { useToast } from '../context/ToastContext';

function formatPaise(p: number) {
  return `₹${(p / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

export default function AdminPanel() {
  const { toast } = useToast();
  const [users, setUsers] = useState<AuditUser[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Freeze Confirmation Modal State
  const [accountToFreeze, setAccountToFreeze] = useState<Account | null>(null);

  // Search & filter
  const [userSearch, setUserSearch] = useState('');
  const [accountSearch, setAccountSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<'ALL' | 'ADMINISTRATOR' | 'ACCOUNT_HOLDER' | 'AUDITOR'>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'FROZEN'>('ALL');

  async function load(quiet = false) {
    if (!quiet) setLoading(true);
    setError(null);
    try {
      const [u, a] = await Promise.all([fetchUsers(), fetchAllAccounts()]);
      setUsers(u);
      setAccounts(a);
      if (quiet) toast.info('System records synced with database.', 'Admin Refresh');
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? 'Failed to load administrator data';
      setError(msg);
      toast.error(msg, 'Load Failed');
    } finally {
      if (!quiet) setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function copyToClipboard(text: string, label: string) {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    toast.success(`${label} copied to clipboard`, 'Copied');
    setTimeout(() => setCopiedId(null), 2000);
  }

  function handleFreezeClick(acc: Account) {
    if (acc.status === 'ACTIVE') {
      // Trigger confirmation modal
      setAccountToFreeze(acc);
    } else {
      // Unfreeze directly
      executeUnfreeze(acc);
    }
  }

  async function executeFreezeConfirmed() {
    if (!accountToFreeze) return;
    const acc = accountToFreeze;
    setBusy(acc.id);
    setAccountToFreeze(null);
    try {
      await freezeAccount(acc.id);
      toast.warning(`Account ${acc.account_number} is now FROZEN. All debits halted.`, 'Account Frozen');
      await load(true);
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? 'Failed to freeze account';
      setError(msg);
      toast.error(msg, 'Operation Refused');
    } finally {
      setBusy(null);
    }
  }

  async function executeUnfreeze(acc: Account) {
    setBusy(acc.id);
    try {
      await unfreezeAccount(acc.id);
      toast.success(`Account ${acc.account_number} has been UNFROZEN and is ACTIVE.`, 'Account Active');
      await load(true);
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? 'Failed to unfreeze account';
      setError(msg);
      toast.error(msg, 'Operation Refused');
    } finally {
      setBusy(null);
    }
  }

  // Filtered lists
  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      if (roleFilter !== 'ALL' && u.role !== roleFilter) return false;
      if (userSearch.trim()) {
        const q = userSearch.toLowerCase();
        return u.email.toLowerCase().includes(q) || u.id.toLowerCase().includes(q);
      }
      return true;
    });
  }, [users, roleFilter, userSearch]);

  const filteredAccounts = useMemo(() => {
    return accounts.filter((a) => {
      if (statusFilter !== 'ALL' && a.status !== statusFilter) return false;
      if (accountSearch.trim()) {
        const q = accountSearch.toLowerCase();
        return (
          a.account_number.toLowerCase().includes(q) ||
          a.account_type.toLowerCase().includes(q) ||
          (a.user_id && a.user_id.toLowerCase().includes(q)) ||
          a.id.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [accounts, statusFilter, accountSearch]);

  // Summary Metrics
  const activeUsersCount = users.filter((u) => u.is_active).length;
  const customerAccounts = accounts.filter((a) => a.account_type === 'CUSTOMER');
  const totalCustomerBalance = customerAccounts.reduce((sum, a) => sum + a.projected_balance_paise, 0);

  return (
    <div className="space-y-8 animate-fade-in text-slate-100">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <span className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-800 text-white flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-500/30">
            <Shield className="w-5 h-5" />
          </span>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Administrator Console
            </h1>
            <p className="text-sm text-slate-400">
              Platform identity management, account freezing controls, and system float oversight.
            </p>
          </div>
        </div>

        <Button variant="secondary" onClick={() => load(true)} className="shadow-xs">
          <RefreshCw className="w-4 h-4 text-slate-400" />
          <span>Refresh All</span>
        </Button>
      </div>

      {error && <Alert kind="error" title="Administrator Alert">{error}</Alert>}

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <Card className="p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Registered Users
            </span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-white">
            {loading ? <Skeleton className="h-8 w-16" /> : users.length}
          </div>
          <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1 mt-1">
            <UserCheck className="w-3 h-3" /> {activeUsersCount} active identities
          </span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Total Accounts
            </span>
            <CreditCard className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-white">
            {loading ? <Skeleton className="h-8 w-16" /> : accounts.length}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            {customerAccounts.length} customer &bull; {accounts.length - customerAccounts.length} clearing
          </span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Customer Liabilities
            </span>
            <span className="text-xs font-bold text-indigo-400 font-mono">INR</span>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-white truncate">
            {loading ? <Skeleton className="h-8 w-28" /> : formatPaise(totalCustomerBalance)}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Aggregated user deposits
          </span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Security Status
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 flex items-center gap-1.5">
            Active
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Argon2 &bull; PyJWT Revocable
          </span>
        </Card>
      </div>

      {/* Admin Analytics Chart */}
      {!loading && <AdminAnalyticsChart accounts={accounts} />}

      {/* Users Section Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="font-bold text-lg text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-400" />
              <span>Identity Directory</span>
              <span className="text-xs bg-slate-800 text-slate-300 font-mono px-2 py-0.5 rounded-full border border-slate-700">
                {filteredUsers.length}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Users enrolled in RBAC roles (Administrator, Auditor, Account Holder).
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Search email or ID..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 text-slate-100 rounded-xl focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition w-48 sm:w-60 placeholder:text-slate-500"
              />
            </div>

            {/* Role Filter Pills */}
            <div className="flex items-center rounded-xl bg-slate-950 border border-slate-800 p-1 text-xs">
              {(['ALL', 'ADMINISTRATOR', 'ACCOUNT_HOLDER', 'AUDITOR'] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRoleFilter(r)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                    roleFilter === r
                      ? 'bg-slate-800 text-white shadow-xs'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {r === 'ALL' ? 'All' : r === 'ADMINISTRATOR' ? 'Admin' : r === 'ACCOUNT_HOLDER' ? 'User' : 'Auditor'}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 bg-slate-950/70 border-b border-slate-800 text-xs uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Active</th>
                <th className="py-3 px-4">Created At</th>
                <th className="py-3 px-4 text-right">User ID (UUID)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-medium text-white">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
                        {u.email[0].toUpperCase()}
                      </div>
                      <span>{u.email}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <Badge
                      tone={
                        u.role === 'ADMINISTRATOR'
                          ? 'info'
                          : u.role === 'AUDITOR'
                          ? 'warning'
                          : 'success'
                      }
                    >
                      {u.role}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-xs">
                    <span
                      className={`inline-flex items-center gap-1 font-semibold ${
                        u.is_active ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {u.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    {new Date(u.created_at).toLocaleString('en-IN', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => copyToClipboard(u.id, 'User ID')}
                      title="Copy User UUID"
                      className="inline-flex items-center gap-1 font-mono text-xs text-indigo-400 hover:text-indigo-300 hover:underline cursor-pointer"
                    >
                      <span>{u.id.slice(0, 8)}...</span>
                      {copiedId === u.id ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-slate-500" />
                      )}
                    </button>
                  </td>
                </tr>
              ))}
              {filteredUsers.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No users matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Accounts Management Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="font-bold text-lg text-white flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-indigo-400" />
              <span>Accounts Ledger & Control</span>
              <span className="text-xs bg-slate-800 text-slate-300 font-mono px-2 py-0.5 rounded-full border border-slate-700">
                {filteredAccounts.length}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Customer balances and platform clearing accounts with freeze capability.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Search account, type, or UUID..."
                value={accountSearch}
                onChange={(e) => setAccountSearch(e.target.value)}
                className="pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 text-slate-100 rounded-xl focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition w-48 sm:w-60 placeholder:text-slate-500"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center rounded-xl bg-slate-950 border border-slate-800 p-1 text-xs">
              {(['ALL', 'ACTIVE', 'FROZEN'] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatusFilter(s)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                    statusFilter === s
                      ? 'bg-slate-800 text-white shadow-xs'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {s === 'ALL' ? 'All' : s === 'ACTIVE' ? 'Active' : 'Frozen'}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 bg-slate-950/70 border-b border-slate-800 text-xs uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Account Number</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Owner ID</th>
                <th className="py-3 px-4 text-right">Projected Balance</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-center">Freeze Control</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredAccounts.map((a) => {
                const isCustomer = a.account_type === 'CUSTOMER';
                const isFrozen = a.status === 'FROZEN';
                return (
                  <tr key={a.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-white text-xs">
                      <div className="flex items-center gap-1.5">
                        <span>{a.account_number}</span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(a.id, 'Account ID')}
                          title="Copy Account UUID"
                          className="p-1 rounded-md text-slate-400 hover:text-indigo-400 transition cursor-pointer"
                        >
                          {copiedId === a.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs font-semibold">
                      <span
                        className={
                          isCustomer
                            ? 'text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 rounded-md'
                            : 'text-slate-300 bg-slate-800 px-2 py-0.5 rounded-md border border-slate-700'
                        }
                      >
                        {a.account_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {a.user_id ? `${a.user_id.slice(0, 8)}...` : '— (System)'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-xs text-white">
                      {formatPaise(a.projected_balance_paise)}
                    </td>
                    <td className="py-3 px-4">
                      <Badge tone={a.status === 'ACTIVE' ? 'success' : 'danger'}>
                        {a.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {isCustomer ? (
                        <Button
                          variant={isFrozen ? 'success' : 'danger'}
                          size="sm"
                          onClick={() => handleFreezeClick(a)}
                          loading={busy === a.id}
                          className="text-xs px-3 py-1 shadow-xs cursor-pointer"
                        >
                          {isFrozen ? (
                            <>
                              <Unlock className="w-3 h-3" />
                              <span>Unfreeze</span>
                            </>
                          ) : (
                            <>
                              <Lock className="w-3 h-3" />
                              <span>Freeze</span>
                            </>
                          )}
                        </Button>
                      ) : (
                        <span className="text-xs text-slate-500 italic">Protected</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {filteredAccounts.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No accounts matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Enhanced Account Freeze Confirmation Modal */}
      <Modal
        open={accountToFreeze !== null}
        onClose={() => setAccountToFreeze(null)}
        title="Confirm Account Freeze"
        subtitle="Operational & Compliance Safeguard"
      >
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-rose-300 text-sm">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Compliance Interlock Warning</span>
            </div>
            <p className="leading-relaxed">
              You are about to freeze account <strong className="font-mono text-white">{accountToFreeze?.account_number}</strong>.
            </p>
            <ul className="list-disc list-inside space-y-1 text-rose-200/90 pt-1">
              <li>All outgoing debit transactions and transfers will be immediately rejected.</li>
              <li>Row-level locking will prevent concurrent overdrafts during status mutation.</li>
              <li>Unfreezing requires an authorized administrator action with full audit logging.</li>
            </ul>
          </div>

          {accountToFreeze && (
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800 text-xs space-y-1.5">
              <div className="flex justify-between text-slate-400">
                <span>Account Number:</span>
                <span className="font-mono text-white font-semibold">{accountToFreeze.account_number}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Account ID (UUID):</span>
                <span className="font-mono text-slate-300 text-[11px]">{accountToFreeze.id}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Current Balance:</span>
                <span className="font-mono text-emerald-400 font-bold">{formatPaise(accountToFreeze.projected_balance_paise)}</span>
              </div>
            </div>
          )}

          <div className="flex gap-2.5 pt-2">
            <Button
              variant="danger"
              onClick={executeFreezeConfirmed}
              loading={busy !== null}
              className="flex-1"
            >
              <Lock className="w-4 h-4" />
              <span>Confirm Account Freeze</span>
            </Button>
            <Button
              variant="secondary"
              onClick={() => setAccountToFreeze(null)}
              disabled={busy !== null}
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
