import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute — guards pages that require authentication.
 *
 * Key fix: when a token exists but the /me fetch is still in-flight (loading=true),
 * we render the spinner rather than immediately redirecting to /login.
 * Without this, completeLogin() sets the token synchronously, navigate('/') fires,
 * ProtectedRoute sees user=null (fetch pending), and bounces the user back to /login.
 */
export function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, token, loading } = useAuth();
  const location = useLocation();

  // Still resolving the session (token present but /me not yet returned) — wait.
  if (loading || (token && !user)) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-400 gap-2.5">
        <span className="animate-spin-slow inline-block w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full" />
        <span className="text-sm font-medium">Authenticating session...</span>
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return <div className="text-center py-24 text-rose-400 font-semibold">Access denied.</div>;
  }
  return <>{children}</>;
}
