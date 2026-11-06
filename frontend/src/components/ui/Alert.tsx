import { type ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

type AlertKind = 'error' | 'success' | 'info' | 'warning';

const alertConfig: Record<AlertKind, { container: string; icon: typeof AlertCircle; iconColor: string }> = {
  error: {
    container: 'bg-rose-950/40 border-rose-800/60 text-rose-200 shadow-rose-950/20',
    icon: AlertCircle,
    iconColor: 'text-rose-400',
  },
  success: {
    container: 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200 shadow-emerald-950/20',
    icon: CheckCircle2,
    iconColor: 'text-emerald-400',
  },
  info: {
    container: 'bg-indigo-950/40 border-indigo-800/60 text-indigo-200 shadow-indigo-950/20',
    icon: Info,
    iconColor: 'text-indigo-400',
  },
  warning: {
    container: 'bg-amber-950/40 border-amber-800/60 text-amber-200 shadow-amber-950/20',
    icon: AlertTriangle,
    iconColor: 'text-amber-400',
  },
};

export function Alert({
  kind = 'error',
  title,
  children,
  className = '',
}: {
  kind?: AlertKind;
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  const conf = alertConfig[kind] || alertConfig.error;
  const Icon = conf.icon;

  return (
    <div
      role="alert"
      className={`flex items-start gap-3 border rounded-2xl p-4 text-sm backdrop-blur-md shadow-xs transition-all ${conf.container} ${className}`}
    >
      <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${conf.iconColor}`} />
      <div className="flex-1 min-w-0">
        {title && <h5 className="font-semibold text-sm mb-0.5 text-white">{title}</h5>}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
