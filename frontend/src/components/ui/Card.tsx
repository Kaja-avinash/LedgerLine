import { type ReactNode } from 'react';

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl shadow-[var(--shadow-card)] border border-slate-200/60 ${className}`}>
      {children}
    </div>
  );
}
