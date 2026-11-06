import { type ReactNode } from 'react';

type Tone = 'success' | 'danger' | 'warning' | 'neutral' | 'info';

const tones: Record<Tone, string> = {
  success: 'bg-emerald-100 text-emerald-700',
  danger: 'bg-rose-100 text-rose-700',
  warning: 'bg-amber-100 text-amber-700',
  neutral: 'bg-slate-100 text-slate-700',
  info: 'bg-indigo-100 text-indigo-700',
};

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: Tone }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}
