interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-shimmer bg-slate-800/60 rounded-lg ${className}`}
      aria-hidden="true"
    />
  );
}

export function AccountCardSkeleton() {
  return (
    <div className="bg-slate-900/70 rounded-3xl p-6 border border-slate-800/80 shadow-sm space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-9 w-44" />
      <div className="pt-2 flex gap-2">
        <Skeleton className="h-9 flex-1 rounded-xl" />
        <Skeleton className="h-9 flex-1 rounded-xl" />
        <Skeleton className="h-9 flex-1 rounded-xl" />
      </div>
    </div>
  );
}

export function StatementTableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-8 w-44 rounded-xl" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center justify-between py-3 border-b border-slate-800/50 gap-4">
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-32" />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-slate-900/70 rounded-3xl p-6 border border-slate-800/80 shadow-sm space-y-4 animate-fade-in">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-5 w-36" />
          <Skeleton className="h-3 w-52" />
        </div>
        <Skeleton className="h-8 w-24 rounded-xl" />
      </div>
      <div className="h-52 w-full rounded-2xl bg-slate-950/60 flex items-end gap-2 p-4">
        <Skeleton className="h-1/3 flex-1 rounded" />
        <Skeleton className="h-1/2 flex-1 rounded" />
        <Skeleton className="h-2/3 flex-1 rounded" />
        <Skeleton className="h-3/4 flex-1 rounded" />
        <Skeleton className="h-1/2 flex-1 rounded" />
        <Skeleton className="h-4/5 flex-1 rounded" />
        <Skeleton className="h-full flex-1 rounded" />
      </div>
    </div>
  );
}
