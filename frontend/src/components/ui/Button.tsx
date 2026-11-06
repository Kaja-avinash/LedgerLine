import { type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

type Variant = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost' | 'outline';
type Size = 'sm' | 'md' | 'lg';

const variants: Record<Variant, string> = {
  primary:
    'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-950/50 hover:from-indigo-500 hover:to-indigo-600 hover:shadow-indigo-500/25 active:from-indigo-700 active:to-indigo-800 border border-indigo-500/40',
  secondary:
    'bg-slate-800/80 text-slate-200 border border-slate-700/80 shadow-xs hover:bg-slate-800 hover:text-white hover:border-slate-600 active:bg-slate-900',
  success:
    'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-md shadow-emerald-950/50 hover:from-emerald-500 hover:to-emerald-600 hover:shadow-emerald-500/25 border border-emerald-500/40',
  danger:
    'bg-gradient-to-r from-rose-600 to-rose-700 text-white shadow-md shadow-rose-950/50 hover:from-rose-500 hover:to-rose-600 hover:shadow-rose-500/25 border border-rose-500/40',
  ghost:
    'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100',
  outline:
    'border border-indigo-500/40 text-indigo-400 hover:bg-indigo-950/50 hover:text-indigo-300',
};

const sizes: Record<Size, string> = {
  sm: 'px-2.5 py-1.5 text-xs rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm rounded-xl gap-2',
  lg: 'px-5 py-2.5 text-base rounded-xl gap-2.5',
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center font-medium transition-all duration-150 cursor-pointer select-none active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
      {children}
    </button>
  );
}
