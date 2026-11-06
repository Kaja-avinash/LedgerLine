import { type ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`bg-slate-900/70 rounded-2xl border border-slate-800/80 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] backdrop-blur-md text-slate-100 transition-all duration-200 ${
        hover ? 'hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgba(0,0,0,0.7)] hover:border-slate-700/80' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}
