import { useState, useMemo } from 'react';
import {
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Calendar,
  Activity,
  Layers,
  PieChart,
} from 'lucide-react';
import type { StatementItem } from '../../lib/ledger';

export type TimeRangeFilter = '7D' | '30D' | '90D' | 'ALL';

interface BalanceTrendChartProps {
  items: StatementItem[];
  currentBalancePaise: number;
  accountNumber?: string;
  timeRange?: TimeRangeFilter;
  onTimeRangeChange?: (range: TimeRangeFilter) => void;
}

export function BalanceTrendChart({
  items,
  currentBalancePaise,
  accountNumber,
  timeRange = 'ALL',
  onTimeRangeChange,
}: BalanceTrendChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Filter items by timeRange if provided
  const timeFilteredItems = useMemo(() => {
    if (timeRange === 'ALL') return items;
    const now = Date.now();
    const days = timeRange === '7D' ? 7 : timeRange === '30D' ? 30 : 90;
    const cutoff = now - days * 24 * 60 * 60 * 1000;
    return items.filter((it) => new Date(it.created_at).getTime() >= cutoff);
  }, [items, timeRange]);

  // Sort chronologically ascending for the chart curve (seq ascending)
  const sorted = useMemo(() => {
    return [...timeFilteredItems].sort((a, b) => a.account_activity_sequence - b.account_activity_sequence);
  }, [timeFilteredItems]);

  // Calculate metrics
  const { totalCredits, totalDebits, creditCount, debitCount, refusalCount } = useMemo(() => {
    let credits = 0;
    let debits = 0;
    let cCount = 0;
    let dCount = 0;
    let rCount = 0;

    for (const it of timeFilteredItems) {
      if (it.kind === 'REFUSAL') {
        rCount++;
      } else if (it.kind === 'POSTING') {
        if (it.entry_type === 'CREDIT') {
          credits += it.amount_paise;
          cCount++;
        } else if (it.entry_type === 'DEBIT') {
          debits += it.amount_paise;
          dCount++;
        }
      }
    }
    return {
      totalCredits: credits,
      totalDebits: debits,
      creditCount: cCount,
      debitCount: dCount,
      refusalCount: rCount,
    };
  }, [timeFilteredItems]);

  // Inflow vs Outflow volumetric proportion
  const totalVolume = totalCredits + totalDebits;
  const creditRatio = totalVolume > 0 ? Math.round((totalCredits / totalVolume) * 100) : 50;
  const debitRatio = totalVolume > 0 ? 100 - creditRatio : 50;

  // Transaction Classification breakdown
  const totalOperationsCount = creditCount + debitCount + refusalCount;
  const depositPct = totalOperationsCount > 0 ? Math.round((creditCount / totalOperationsCount) * 100) : 0;
  const withdrawPct = totalOperationsCount > 0 ? Math.round((debitCount / totalOperationsCount) * 100) : 0;
  const refusalPct = totalOperationsCount > 0 ? Math.round((refusalCount / totalOperationsCount) * 100) : 0;

  // Points for chart
  const points = useMemo(() => {
    if (sorted.length === 0) {
      return [
        { x: 0, y: currentBalancePaise, label: 'Initial', seq: 0, date: 'Baseline', item: null },
        { x: 1, y: currentBalancePaise, label: 'Current', seq: 0, date: 'Now', item: null },
      ];
    }

    const pts = sorted.map((it, idx) => ({
      x: idx,
      y: it.running_balance_paise,
      label: `#${it.account_activity_sequence}`,
      seq: it.account_activity_sequence,
      date: new Date(it.created_at).toLocaleString('en-IN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
      item: it,
    }));

    if (pts.length === 1) {
      return [
        { x: -1, y: 0, label: 'Start', seq: 0, date: 'Start', item: null },
        pts[0],
      ];
    }

    return pts;
  }, [sorted, currentBalancePaise]);

  // SVG coordinate dimensions
  const svgWidth = 800;
  const svgHeight = 220;
  const paddingX = 40;
  const paddingY = 30;

  const minY = Math.min(0, ...points.map((p) => p.y));
  const maxY = Math.max(10000, ...points.map((p) => p.y)) * 1.1; // 10% headroom

  const getSvgX = (index: number) => {
    if (points.length <= 1) return paddingX;
    return paddingX + (index / (points.length - 1)) * (svgWidth - paddingX * 2);
  };

  const getSvgY = (val: number) => {
    if (maxY === minY) return svgHeight / 2;
    const norm = (val - minY) / (maxY - minY);
    return svgHeight - paddingY - norm * (svgHeight - paddingY * 2);
  };

  // Generate smooth SVG path (Catmull-Rom / Bezier curve)
  const linePath = useMemo(() => {
    if (points.length < 2) return '';
    const coords = points.map((p, i) => ({ x: getSvgX(i), y: getSvgY(p.y) }));

    let d = `M ${coords[0].x} ${coords[0].y}`;
    for (let i = 0; i < coords.length - 1; i++) {
      const p0 = coords[i === 0 ? 0 : i - 1];
      const p1 = coords[i];
      const p2 = coords[i + 1];
      const p3 = coords[i + 2 < coords.length ? i + 2 : i + 1];

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }
    return d;
  }, [points, minY, maxY]);

  const areaPath = useMemo(() => {
    if (!linePath) return '';
    const lastX = getSvgX(points.length - 1);
    const firstX = getSvgX(0);
    const bottomY = svgHeight - paddingY;
    return `${linePath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
  }, [linePath, points]);

  const activePoint = hoveredIndex !== null ? points[hoveredIndex] : points[points.length - 1];
  const activeX = hoveredIndex !== null ? getSvgX(hoveredIndex) : getSvgX(points.length - 1);
  const activeY = activePoint ? getSvgY(activePoint.y) : svgHeight / 2;

  const formatPaise = (p: number) => `₹${(p / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  return (
    <div className="bg-slate-900/70 rounded-3xl border border-slate-800/80 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] backdrop-blur-md p-6 transition-all text-slate-100 space-y-6">
      {/* Header Row: Title, Account Chip & Time-Range Filter Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-7 h-7 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <TrendingUp className="w-4 h-4" />
            </span>
            <h3 className="font-bold text-white text-lg">Balance Analytics & Cash Flow</h3>
            {accountNumber && (
              <span className="text-xs bg-slate-800 text-slate-300 font-mono px-2 py-0.5 rounded-lg border border-slate-700">
                {accountNumber}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            Real-time projected running balance and double-entry activity sequence.
          </p>
        </div>

        {/* Time-Range Filter Toggle Pills */}
        <div className="flex items-center gap-2">
          {onTimeRangeChange && (
            <div className="flex items-center rounded-xl bg-slate-950 border border-slate-800 p-1 text-xs">
              {(['7D', '30D', '90D', 'ALL'] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => onTimeRangeChange(r)}
                  className={`px-3 py-1 rounded-lg font-semibold transition cursor-pointer ${
                    timeRange === r
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  {r === 'ALL' ? 'All Time' : r}
                </button>
              ))}
            </div>
          )}

          {/* Micro KPI pills */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300">
              <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs text-emerald-400/80 font-medium hidden sm:inline">Inflow:</span>
              <span className="text-xs font-bold font-mono">+{formatPaise(totalCredits)}</span>
            </div>

            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300">
              <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-xs text-rose-400/80 font-medium hidden sm:inline">Outflow:</span>
              <span className="text-xs font-bold font-mono">-{formatPaise(totalDebits)}</span>
            </div>

            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-800/60 text-indigo-300">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-xs text-indigo-400/80 font-medium hidden sm:inline">Ops:</span>
              <span className="text-xs font-bold font-mono">{timeFilteredItems.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Ratios & Volume Proportion Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
        {/* Inflow vs Outflow Ratio Indicator */}
        <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/90 text-xs space-y-2">
          <div className="flex justify-between items-center text-slate-300">
            <span className="font-semibold flex items-center gap-1.5">
              <PieChart className="w-3.5 h-3.5 text-indigo-400" />
              <span>Inflow vs. Outflow Volumetric Ratio</span>
            </span>
            <span className="font-mono text-slate-400 font-medium">
              <strong className="text-emerald-400">{creditRatio}%</strong> In /{' '}
              <strong className="text-rose-400">{debitRatio}%</strong> Out
            </span>
          </div>

          {/* Dual-color split progress bar */}
          <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden flex border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
              style={{ width: `${totalVolume > 0 ? creditRatio : 50}%` }}
              title={`Inflow: ${creditRatio}%`}
            />
            <div
              className="h-full bg-gradient-to-r from-rose-500 to-rose-400 transition-all duration-500"
              style={{ width: `${totalVolume > 0 ? debitRatio : 50}%` }}
              title={`Outflow: ${debitRatio}%`}
            />
          </div>

          <div className="flex justify-between text-[11px] text-slate-400 pt-0.5">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Total Credits: <strong>{formatPaise(totalCredits)}</strong></span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span>Total Debits: <strong>{formatPaise(totalDebits)}</strong></span>
            </span>
          </div>
        </div>

        {/* Transaction Classification Breakdown Bar */}
        <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/90 text-xs space-y-2">
          <div className="flex justify-between items-center text-slate-300">
            <span className="font-semibold flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span>Transaction Classification Breakdown</span>
            </span>
            <span className="font-mono text-slate-400 font-medium">
              {totalOperationsCount} Operations
            </span>
          </div>

          {/* Segmented volumetric progress bar */}
          <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden flex border border-slate-800">
            {totalOperationsCount === 0 ? (
              <div className="h-full w-full bg-slate-800" />
            ) : (
              <>
                <div
                  className="h-full bg-emerald-500 transition-all duration-500"
                  style={{ width: `${depositPct}%` }}
                  title={`Credits: ${creditCount} (${depositPct}%)`}
                />
                <div
                  className="h-full bg-rose-500 transition-all duration-500"
                  style={{ width: `${withdrawPct}%` }}
                  title={`Debits: ${debitCount} (${withdrawPct}%)`}
                />
                <div
                  className="h-full bg-amber-500 transition-all duration-500"
                  style={{ width: `${refusalPct}%` }}
                  title={`Refusals: ${refusalCount} (${refusalPct}%)`}
                />
              </>
            )}
          </div>

          <div className="flex items-center gap-3 text-[11px] text-slate-400 pt-0.5">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Deposits ({creditCount})</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span>Debits ({debitCount})</span>
            </span>
            {refusalCount > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>Refusals ({refusalCount})</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* SVG Interactive Chart Canvas */}
      <div className="relative w-full overflow-hidden select-none pt-2">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-48 sm:h-56 overflow-visible"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="balanceGradientDark" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
              <stop offset="70%" stopColor="#4f46e5" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="lineStrokeDark" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="50%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#a5b4fc" />
            </linearGradient>
            <filter id="glowDark" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#6366f1" floodOpacity="0.45" />
            </filter>
          </defs>

          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = paddingY + pct * (svgHeight - paddingY * 2);
            const valueAtLine = maxY - pct * (maxY - minY);
            return (
              <g key={idx}>
                <line
                  x1={paddingX}
                  y1={y}
                  x2={svgWidth - paddingX}
                  y2={y}
                  stroke="#1e293b"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={paddingX - 8}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="10"
                  fill="#64748b"
                  fontFamily="monospace"
                >
                  ₹{(valueAtLine / 100).toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Area Fill */}
          {areaPath && <path d={areaPath} fill="url(#balanceGradientDark)" />}

          {/* Smooth Curve Stroke */}
          {linePath && (
            <path
              d={linePath}
              fill="none"
              stroke="url(#lineStrokeDark)"
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#glowDark)"
            />
          )}

          {/* Vertical Guide & Hover marker */}
          {activePoint && (
            <g>
              <line
                x1={activeX}
                y1={paddingY}
                x2={activeX}
                y2={svgHeight - paddingY}
                stroke="#818cf8"
                strokeWidth="1.5"
                strokeDasharray="3 3"
                opacity="0.7"
              />
              <circle
                cx={activeX}
                cy={activeY}
                r="6"
                fill="#0f172a"
                stroke="#818cf8"
                strokeWidth="3"
                className="transition-all duration-75"
              />
            </g>
          )}

          {/* Invisible interactive hover hit areas along X axis */}
          {points.map((_, idx) => {
            const colWidth = (svgWidth - paddingX * 2) / Math.max(1, points.length - 1);
            const colLeft = getSvgX(idx) - colWidth / 2;
            return (
              <rect
                key={idx}
                x={Math.max(0, colLeft)}
                y={0}
                width={colWidth}
                height={svgHeight}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIndex(idx)}
              />
            );
          })}
        </svg>

        {/* Floating Tooltip Pill */}
        {activePoint && (
          <div
            className="absolute top-2 pointer-events-none transition-all duration-100 ease-out z-10"
            style={{
              left: `${Math.min(Math.max((activeX / svgWidth) * 100, 15), 85)}%`,
              transform: 'translateX(-50%)',
            }}
          >
            <div className="bg-slate-950/95 backdrop-blur-md text-white text-xs py-2 px-3.5 rounded-xl shadow-2xl border border-slate-700/80 flex items-center gap-3">
              <div>
                <span className="text-slate-400 block text-[10px]">
                  {activePoint.item ? `Seq #${activePoint.seq} • ${activePoint.date}` : activePoint.date}
                </span>
                <span className="font-bold text-sm font-mono text-indigo-300">
                  {formatPaise(activePoint.y)}
                </span>
              </div>
              {activePoint.item && (
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                    activePoint.item.entry_type === 'CREDIT'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  }`}
                >
                  {activePoint.item.entry_type === 'CREDIT' ? '+' : '-'}
                  {formatPaise(activePoint.item.amount_paise)}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Axis Guide */}
      <div className="flex justify-between items-center text-[11px] text-slate-400 border-t border-slate-800/80 pt-3">
        <span className="flex items-center gap-1 text-slate-400">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          {points[0]?.date ?? 'Start'}
        </span>
        <span className="text-slate-400 font-medium">
          {timeFilteredItems.length > 0 ? `${timeFilteredItems.length} posting events in view (${timeRange})` : 'No events in selected timeframe'}
        </span>
        <span className="text-slate-400">Latest: {points[points.length - 1]?.date ?? 'Now'}</span>
      </div>
    </div>
  );
}
