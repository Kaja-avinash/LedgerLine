import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Wallet } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';

export default function Login() {
  const { completeLogin } = useAuth();
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
      } else {
        completeLogin(res.data.access_token);
        navigate('/');
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Login failed');
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
      completeLogin(res.data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Invalid OTP');
    } finally {
      setSubmitting(false);
    }
  }

  if (otpEmail) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-[var(--shadow-card)] border border-border p-8 animate-fade-in">
          <h1 className="text-2xl font-semibold mb-2">Verify your identity</h1>
          <p className="text-sm text-muted mb-6">
            We sent a 6-digit code to <strong className="text-ink">{otpEmail}</strong>. It expires in 5 minutes.
          </p>
          {error && <div className="mb-4"><Alert kind="error">{error}</Alert></div>}
          <form onSubmit={onVerifyOtp} className="space-y-4">
            <Input
              label="OTP Code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="text-center tracking-[0.4em] text-lg"
            />
            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? 'Verifying...' : 'Verify code'}
            </Button>
            <button
              type="button"
              onClick={() => {
                setOtpEmail(null);
                setOtp('');
                setError(null);
              }}
              className="w-full text-sm text-muted hover:text-ink"
            >
              Back to login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-[var(--shadow-card)] border border-border p-8 animate-fade-in">
        <div className="flex items-center gap-2 mb-6">
          <span className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center">
            <Wallet className="w-5 h-5 text-white" />
          </span>
          <h1 className="text-2xl font-semibold">Sign in to LedgerLine</h1>
        </div>

        <div className="flex mb-6 rounded-lg bg-slate-100 p-1">
          {([
            { value: 'ACCOUNT_HOLDER' as const, label: 'User' },
            { value: 'ADMINISTRATOR' as const, label: 'Admin' },
            { value: 'AUDITOR' as const, label: 'Auditor' },
          ]).map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setRole(opt.value)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition ${
                role === opt.value ? 'bg-white text-brand-700 shadow-sm' : 'text-muted hover:text-ink'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {error && <div className="mb-4"><Alert kind="error">{error}</Alert></div>}
        <form onSubmit={onSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPw ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowPw((s) => !s)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
        <p className="mt-4 text-sm text-muted">
          No account?{' '}
          <Link to="/register" className="text-brand-600 hover:underline font-medium">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
