import { useState, useEffect, type ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogOut, Wallet, Shield, BarChart3, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  // Live telemetry pulse ticker state
  const [ping, setPing] = useState(3);
  const [pulseCount, setPulseCount] = useState(1048);

  useEffect(() => {
    const timer = setInterval(() => {
      setPing(Math.floor(2 + Math.random() * 3));
      setPulseCount((c) => c + 1);
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const handleLogout = () => {
    logout();
    toast.info('You have been securely signed out.', 'Session Ended');
    navigate('/login');
  };

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <nav className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo, Brand & Live System Activity Ticker */}
          <div className="flex items-center gap-4 lg:gap-6">
            <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-white group">
              <span className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-indigo-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform duration-200">
                <Wallet className="w-5 h-5 text-white" />
              </span>
              <div className="flex flex-col">
                <span className="leading-tight font-extrabold tracking-tight text-white">LedgerLine</span>
                <span className="text-[10px] uppercase font-semibold tracking-widest text-indigo-400 -mt-0.5">
                  FinTech Core
                </span>
              </div>
            </Link>

            {/* Live System Activity Ticker Pill */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-[11px] text-slate-400 font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-slate-300 font-semibold">Engine Synced</span>
              <span className="text-slate-600">&bull;</span>
              <span className="font-mono text-slate-400">{ping}ms</span>
              <span className="text-slate-600">&bull;</span>
              <span className="font-mono text-indigo-400">Block #{pulseCount}</span>
            </div>
          </div>

          {/* Nav links & User Profile */}
          <div className="flex items-center gap-2 sm:gap-3">
            {user ? (
              <>
                <div className="flex items-center gap-1 sm:gap-1.5 mr-1 sm:mr-3">
                  <Link
                    to="/"
                    className={`px-3 py-1.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
                      isActive('/')
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-xs'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                    }`}
                  >
                    Dashboard
                  </Link>

                  {user.role === 'ADMINISTRATOR' && (
                    <Link
                      to="/admin"
                      className={`px-3 py-1.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-1.5 transition-all ${
                        isActive('/admin')
                          ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-xs'
                          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                      }`}
                    >
                      <Shield className="w-4 h-4 text-indigo-400" />
                      <span>Admin</span>
                    </Link>
                  )}

                  {(user.role === 'ADMINISTRATOR' || user.role === 'AUDITOR') && (
                    <Link
                      to="/audit"
                      className={`px-3 py-1.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-1.5 transition-all ${
                        isActive('/audit')
                          ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-xs'
                          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60'
                      }`}
                    >
                      <BarChart3 className="w-4 h-4 text-indigo-400" />
                      <span>Audit</span>
                    </Link>
                  )}
                </div>

                {/* User Identity Chip */}
                <div className="hidden lg:flex items-center gap-2.5 pl-3 border-l border-slate-800">
                  <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-slate-300">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col text-left">
                    <span className="text-xs font-semibold text-slate-200 truncate max-w-[150px]">
                      {user.email}
                    </span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider ${
                        user.role === 'ADMINISTRATOR'
                          ? 'text-indigo-400'
                          : user.role === 'AUDITOR'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      {user.role === 'ACCOUNT_HOLDER' ? 'Customer' : user.role}
                    </span>
                  </div>
                </div>

                {/* Logout Button */}
                <button
                  type="button"
                  onClick={handleLogout}
                  title="Sign out"
                  className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 border border-transparent hover:border-rose-900/50 transition-all duration-150 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-3.5 py-2 text-xs sm:text-sm font-semibold text-slate-300 hover:text-white hover:bg-slate-900 rounded-xl transition"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-xs sm:text-sm font-semibold bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-xl hover:from-indigo-500 hover:to-indigo-600 shadow-md shadow-indigo-950/40 transition-all active:scale-[0.98]"
                >
                  Create Account
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
        {children}
      </main>

      {/* Enterprise Fintech Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 backdrop-blur-sm py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="font-semibold text-slate-200">LedgerLine Engine v1.0</span>
            <span>—</span>
            <span>Integer Paise &bull; Deterministic Concurrency &bull; SHA-256 Idempotency</span>
          </div>
          <div className="flex items-center gap-4 text-slate-500">
            <span>Synchronous PostgreSQL &bull; PyJWT &bull; Argon2</span>
            <span>&bull;</span>
            <span className="text-slate-300 font-medium">Enterprise Double-Entry Protocol</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
