import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';

export default function Login() {
  const { login, completeLogin } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<'ACCOUNT_HOLDER' | 'ADMINISTRATOR'>('ACCOUNT_HOLDER');
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
        // fallback: direct token (shouldn't happen)
        await login(email, password);
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
      const token = res.data.access_token as string;
      completeLogin(token);
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Invalid OTP');
    } finally {
      setSubmitting(false);
    }
  }

  if (otpEmail) {
    return (
      <div className="max-w-md mx-auto bg-white rounded-lg shadow p-8">
        <h1 className="text-2xl font-semibold mb-2">Enter verification code</h1>
        <p className="text-sm text-slate-600 mb-6">
          We sent a 6-digit code to <strong>{otpEmail}</strong>. It expires in 5 minutes.
        </p>
        {error && <div className="mb-4 text-sm text-red-600">{error}</div>}
        <form onSubmit={onVerifyOtp} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">OTP Code</label>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="w-full border border-slate-300 rounded px-3 py-2 text-center tracking-widest text-lg"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? 'Verifying...' : 'Verify'}
          </button>
          <button
            type="button"
            onClick={() => {
              setOtpEmail(null);
              setOtp('');
              setError(null);
            }}
            className="w-full text-sm text-slate-500 hover:text-slate-700"
          >
            Back
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow p-8">
      <h1 className="text-2xl font-semibold mb-6">Sign in</h1>

      {/* Role toggle */}
      <div className="flex mb-6 border border-slate-200 rounded overflow-hidden">
        <button
          type="button"
          onClick={() => setRole('ACCOUNT_HOLDER')}
          className={`flex-1 py-2 text-sm ${role === 'ACCOUNT_HOLDER' ? 'bg-indigo-600 text-white' : 'bg-white text-slate-600'}`}
        >
          User Login
        </button>
        <button
          type="button"
          onClick={() => setRole('ADMINISTRATOR')}
          className={`flex-1 py-2 text-sm ${role === 'ADMINISTRATOR' ? 'bg-indigo-600 text-white' : 'bg-white text-slate-600'}`}
        >
          Admin Login
        </button>
      </div>

      {error && <div className="mb-4 text-sm text-red-600">{error}</div>}
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <div className="relative">
            <input
              type={showPw ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-slate-300 rounded px-3 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              onClick={() => setShowPw((s) => !s)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500"
            >
              {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        No account?{' '}
        <Link to="/register" className="text-indigo-600 hover:underline">
          Register
        </Link>
      </p>
    </div>
  );
}
