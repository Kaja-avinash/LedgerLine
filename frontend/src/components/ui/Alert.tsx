import { type ReactNode } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export function Alert({ kind = 'error', children }: { kind?: 'error' | 'success'; children: ReactNode }) {
  const styles =
    kind === 'error'
      ? 'bg-rose-50 border-rose-200 text-rose-700'
      : 'bg-emerald-50 border-emerald-200 text-emerald-700';
  const Icon = kind === 'error' ? AlertCircle : CheckCircle2;
  return (
    <div className={`flex items-start gap-2 border rounded-lg px-3 py-2 text-sm ${styles}`}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
      <div>{children}</div>
    </div>
  );
}
