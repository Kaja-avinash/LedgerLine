import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Wallet, ArrowRight, Lock, Mail, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { api } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';

export default function Login() {
  const { completeLogin } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [role, setRole] = useState<'ACCOUNT_HOLDER' | 'ADMINISTRATOR' | 'AUDITOR'>('ACCOUNT_HOLDER');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [otp, setOtp] = useState('');
  const [otpEmail, setOtpEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.post(
        '/api/auth/login',
        new URLSearchParams({ username: email, password, role }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
      );
      if (res.data.status === 'otp_required') {
        setOtpEmail(res.data.email);
        toast.info(`A 6-digit security OTP was sent to ${res.data.email}`, 'OTP Code Dispatched');
      } else {
        toast.success(`Authenticated as ${role.toLowerCase().replace('_', ' ')}`, 'Access Granted');
        completeLogin(res.data.access_token);
        navigate('/');
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Authentication failed. Please verify credentials.';
      setError(msg);
      toast.error(msg, 'Authentication Failed');
    } finally {
      setSubmitting(false);
    }
  }

  async function onVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.post('/api/auth/verify-otp', { email: otpEmail, otp });
      toast.success('Identity verified with live OTP.', 'Verification Succeeded');
      completeLogin(res.data.access_token);
      navigate('/');
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Invalid or expired OTP code';
      setError(msg);
      toast.error(msg, 'Verification Error');
    } finally {
      setSubmitting(false);
    }
  }

  if (otpEmail) {
    return (
      <div className="min-h-[75vh] flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-slate-900/90 rounded-3xl shadow-2xl border border-slate-800 p-8 sm:p-10 animate-fade-in backdrop-blur-md text-slate-100">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center mb-5">
            <KeyRound className="w-6 h-6" />
          </div>

          <h1 className="text-2xl font-extrabold text-white tracking-tight mb-1.5">
            Two-Factor Verification
          </h1>
          <p className="text-xs text-slate-400 mb-6 leading-relaxed">
            We dispatched a 6-digit cryptographic OTP to{' '}
            <strong className="text-slate-200 font-mono">{otpEmail}</strong>. Please enter it below.
          </p>

          {error && <div className="mb-4"><Alert kind="error">{error}</Alert></div>}

          <form onSubmit={onVerifyOtp} className="space-y-5">
            <Input
              label="6-Digit OTP Code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              autoFocus
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="text-center tracking-[0.5em] text-xl font-mono font-bold"
              placeholder="••••••"
            />

            <Button type="submit" loading={submitting} className="w-full py-2.5">
              {submitting ? 'Verifying OTP...' : 'Verify & Continue'}
            </Button>

            <button
              type="button"
              onClick={() => {
                setOtpEmail(null);
                setOtp('');
                setError(null);
              }}
              className="w-full text-xs text-slate-400 hover:text-white transition py-1 font-medium cursor-pointer"
            >
              &larr; Back to credential login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900/90 rounded-3xl shadow-2xl border border-slate-800 p-8 sm:p-10 animate-fade-in relative overflow-hidden backdrop-blur-md text-slate-100">
        {/* Subtle decorative glow */}
        <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-indigo-500/15 via-purple-500/10 to-transparent rounded-bl-full pointer-events-none" />

        {/* Brand Header */}
        <div className="flex items-center gap-3 mb-6">
          <span className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-indigo-800 flex items-center justify-center shadow-lg shadow-indigo-500/25 border border-indigo-500/30 text-white">
            <Wallet className="w-5 h-5" />
          </span>
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-tight leading-none">
              Sign in to LedgerLine
            </h1>
            <span className="text-[11px] font-semibold text-slate-400">Enterprise Financial Core</span>
          </div>
        </div>

        {/* Role Switcher Pill Bar */}
        <div className="mb-6">
          <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
            Select Role Profile
          </label>
          <div className="flex rounded-xl bg-slate-950 border border-slate-800 p-1">
            {([
              { value: 'ACCOUNT_HOLDER' as const, label: 'Customer' },
              { value: 'ADMINISTRATOR' as const, label: 'Admin' },
              { value: 'AUDITOR' as const, label: 'Auditor' },
            ]).map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setRole(opt.value)}
                className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all duration-150 cursor-pointer ${
                  role === opt.value
                    ? 'bg-slate-850 text-indigo-300 shadow-xs border border-slate-750'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {opt.label}
              </button>
            ))}
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
              Password
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type={showPw ? 'text' : 'password'}
                required
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
          </div>

          <Button type="submit" loading={submitting} className="w-full py-2.5 mt-2">
            <span>{submitting ? 'Authenticating...' : 'Sign in to Console'}</span>
            {!submitting && <ArrowRight className="w-4 h-4" />}
          </Button>
        </form>

        {/* Footer Link */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>Need a new account?</span>
          <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-bold hover:underline">
            Register as Customer &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
