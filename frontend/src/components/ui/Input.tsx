import { type InputHTMLAttributes, type ReactNode } from 'react';

export function Input({
  label,
  icon,
  error,
  helperText,
  className = '',
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  icon?: ReactNode;
  error?: string;
  helperText?: string;
  className?: string;
}) {
  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
          {label}
        </label>
      )}
      <div className="relative rounded-xl shadow-xs">
        {icon && (
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none">
            {icon}
          </span>
        )}
        <input
          className={`w-full rounded-xl border bg-slate-950/80 px-3.5 py-2.5 text-sm text-slate-100 transition-all duration-150 placeholder:text-slate-500 focus:outline-none focus:ring-4 ${
            error
              ? 'border-rose-500/60 focus:border-rose-500 focus:ring-rose-500/15'
              : 'border-slate-800 focus:border-indigo-500 focus:ring-indigo-500/15 hover:border-slate-700'
          } ${icon ? 'pl-10' : ''} ${className}`}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-rose-400 font-medium">{error}</p>}
      {helperText && !error && <p className="text-xs text-slate-400">{helperText}</p>}
    </div>
  );
}
