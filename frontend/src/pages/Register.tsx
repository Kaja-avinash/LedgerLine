import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Wallet, ArrowRight, Lock, Mail, ShieldCheck } from 'lucide-react';
import { api } from '../lib/api';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';

export default function Register() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post('/api/auth/register', { email, password, role: 'ACCOUNT_HOLDER' });
      toast.success('Your customer account was successfully created! Please sign in.', 'Account Enrolled');
      navigate('/login');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : 'Registration failed. Please check requirements.';
      setError(msg);
      toast.error(msg, 'Enrollment Failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900/90 rounded-3xl shadow-2xl border border-slate-800 p-8 sm:p-10 animate-fade-in relative overflow-hidden backdrop-blur-md text-slate-100">
        {/* Decorative background glow */}
        <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-emerald-500/15 via-indigo-500/10 to-transparent rounded-bl-full pointer-events-none" />

        {/* Brand Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-indigo-800 flex items-center justify-center shadow-lg shadow-indigo-500/25 border border-indigo-500/30 text-white">
            <Wallet className="w-5 h-5" />
          </span>
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-tight leading-none">
              Create Customer Account
            </h1>
            <span className="text-[11px] font-semibold text-slate-400">LedgerLine FinTech Network</span>
          </div>
        </div>

        {error && <div className="mb-5"><Alert kind="error">{error}</Alert></div>}

        <form onSubmit={onSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            required
            icon={<Mail className="w-4 h-4 text-slate-500" />}
            placeholder="you@domain.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Password (min 8 characters)
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type={showPw ? 'text' : 'password'}
                required
                minLength={8}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/80 pl-10 pr-10 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/15 focus:border-indigo-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowPw((s) => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white p-1 cursor-pointer"
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Hashed with Argon2id before storage in database</span>
            </p>
          </div>

          <Button type="submit" loading={submitting} className="w-full py-2.5 mt-2">
            <span>{submitting ? 'Creating Account...' : 'Open Account'}</span>
            {!submitting && <ArrowRight className="w-4 h-4" />}
          </Button>
        </form>

        {/* Footer Link */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>Already registered?</span>
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-bold hover:underline">
            Sign in &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
