import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  title?: string;
  duration?: number;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType, title?: string, duration?: number) => void;
  toast: {
    success: (message: string, title?: string, duration?: number) => void;
    error: (message: string, title?: string, duration?: number) => void;
    info: (message: string, title?: string, duration?: number) => void;
    warning: (message: string, title?: string, duration?: number) => void;
  };
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = 'info', title?: string, duration = 4200) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastItem = { id, type, message, title, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const toastMethods = {
    success: (msg: string, title?: string, dur?: number) => showToast(msg, 'success', title, dur),
    error: (msg: string, title?: string, dur?: number) => showToast(msg, 'error', title, dur),
    info: (msg: string, title?: string, dur?: number) => showToast(msg, 'info', title, dur),
    warning: (msg: string, title?: string, dur?: number) => showToast(msg, 'warning', title, dur),
  };

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />,
    error: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />,
    info: <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />,
  };

  const borders = {
    success: 'border-emerald-500/30 bg-slate-900/95 shadow-emerald-950/40 text-slate-100',
    error: 'border-rose-500/30 bg-slate-900/95 shadow-rose-950/40 text-slate-100',
    warning: 'border-amber-500/30 bg-slate-900/95 shadow-amber-950/40 text-slate-100',
    info: 'border-indigo-500/30 bg-slate-900/95 shadow-indigo-950/40 text-slate-100',
  };

  const progressColors = {
    success: 'bg-emerald-500',
    error: 'bg-rose-500',
    warning: 'bg-amber-500',
    info: 'bg-indigo-500',
  };

  return (
    <ToastContext.Provider value={{ showToast, toast: toastMethods }}>
      {children}
      {/* Toast container */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            aria-live="polite"
            className={`pointer-events-auto relative overflow-hidden rounded-2xl border p-4 shadow-2xl backdrop-blur-md animate-toast-in transition-all duration-200 ${borders[t.type]}`}
          >
            <div className="flex items-start gap-3">
              {icons[t.type]}
              <div className="flex-1 min-w-0 pr-2">
                {t.title && <h4 className="text-sm font-semibold text-white mb-0.5">{t.title}</h4>}
                <p className="text-xs text-slate-300 leading-relaxed break-words">{t.message}</p>
              </div>
              <button
                type="button"
                onClick={() => removeToast(t.id)}
                aria-label="Close notification"
                className="text-slate-400 hover:text-white transition p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {/* Auto-dismiss progress bar */}
            {t.duration && t.duration > 0 && (
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-slate-800">
                <div
                  className={`h-full ${progressColors[t.type]} transition-all linear`}
                  style={{
                    animation: `shrinkWidth ${t.duration}ms linear forwards`,
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
      <style>{`
        @keyframes shrinkWidth {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
