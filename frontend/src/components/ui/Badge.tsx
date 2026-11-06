import { type ReactNode } from 'react';

type Tone = 'success' | 'danger' | 'warning' | 'neutral' | 'info' | 'purple';

const tones: Record<Tone, { badge: string; dot: string }> = {
  success: {
    badge: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
    dot: 'bg-emerald-400',
  },
  danger: {
    badge: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
    dot: 'bg-rose-400',
  },
  warning: {
    badge: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
    dot: 'bg-amber-400',
  },
  neutral: {
    badge: 'bg-slate-800/80 text-slate-300 border border-slate-700/80',
    dot: 'bg-slate-400',
  },
  info: {
    badge: 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30',
    dot: 'bg-indigo-400',
  },
  purple: {
    badge: 'bg-purple-500/15 text-purple-300 border border-purple-500/30',
    dot: 'bg-purple-400',
  },
};

export function Badge({
  children,
  tone = 'neutral',
  dot = true,
  className = '',
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  className?: string;
}) {
  const t = tones[tone] || tones.neutral;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide ${t.badge} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${t.dot}`} />}
      {children}
    </span>
  );
}
