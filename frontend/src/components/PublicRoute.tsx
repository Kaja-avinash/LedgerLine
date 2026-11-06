import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * PublicRoute — wraps routes that should only be accessible when logged OUT.
 *
 * If a user is already authenticated (user object resolved) and tries to visit
 * /login or /register, they are immediately redirected to the dashboard (/).
 * While the session is still being resolved (loading or token-but-no-user),
 * we render a neutral loading state so we never flash the wrong page.
 */
export function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, token, loading } = useAuth();

  // Session still resolving — don't flash the login form for authenticated users.
  if (loading || (token && !user)) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-400 gap-2.5">
        <span className="animate-spin-slow inline-block w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full" />
        <span className="text-sm font-medium">Resolving identity...</span>
      </div>
    );
  }

  // Already authenticated — bounce to dashboard.
  if (user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
