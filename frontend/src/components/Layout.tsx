import { Link, useNavigate } from 'react-router-dom';
import { LogOut, Wallet, Shield, BarChart3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg text-ink">
            <span className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <Wallet className="w-4 h-4 text-white" />
            </span>
            LedgerLine
          </Link>
          <div className="flex items-center gap-3">
            {user ? (
              <>
                {user.role === 'ADMINISTRATOR' && (
                  <>
                    <Link to="/admin" className="text-sm text-muted hover:text-ink flex items-center gap-1">
                      <Shield className="w-4 h-4" /> Admin
                    </Link>
                    <Link to="/audit" className="text-sm text-muted hover:text-ink flex items-center gap-1">
                      <BarChart3 className="w-4 h-4" /> Audit
                    </Link>
                  </>
                )}
                {user.role === 'AUDITOR' && (
                  <Link to="/audit" className="text-sm text-muted hover:text-ink flex items-center gap-1">
                    <BarChart3 className="w-4 h-4" /> Audit
                  </Link>
                )}
                <span className="text-sm text-muted hidden sm:inline">
                  {user.email}
                  <span className="ml-1 text-xs text-slate-400">({user.role})</span>
                </span>
                <button
                  onClick={() => {
                    logout();
                    navigate('/login');
                  }}
                  className="flex items-center gap-1 text-sm text-muted hover:text-ink"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm text-muted hover:text-ink">Sign in</Link>
                <Link
                  to="/register"
                  className="text-sm bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-6 py-8 animate-fade-in">{children}</main>
      <footer className="max-w-6xl mx-auto px-6 py-6 text-xs text-muted">
        LedgerLine — money movement with a ledger you can prove.
      </footer>
    </div>
  );
}
