import type { FileRecord } from "@/lib/mockData";
import { getRiskBg, getRiskColor, getRiskLabel } from "@/lib/mockData";

interface FileDetailProps {
  file: FileRecord | null;
}

interface MetricRowProps {
  label: string;
  value: string | number;
  highlight?: boolean;
  color?: string;
}

function MetricRow({ label, value, highlight, color }: MetricRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-800/70 py-2.5 last:border-0">
      <span className="text-xs text-slate-500">{label}</span>
      <span
        className={`font-mono text-sm font-semibold ${
          color ? "" : highlight ? "text-slate-200" : "text-slate-400"
        }`}
        style={color ? { color } : undefined}
      >
        {value}
      </span>
    </div>
  );
}

export default function FileDetail({ file }: FileDetailProps) {
  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-700/50 bg-slate-900/30 p-10 text-center">
        <svg
          width="28" height="28" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="1.5"
          className="text-slate-700"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
        <p className="text-xs text-slate-600">
          Select a file to view its health report
        </p>
      </div>
    );
  }

  const color = getRiskColor(file.riskLevel);

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 overflow-hidden">
      {/* Header */}
      <div
        className="flex items-start justify-between gap-4 border-b border-slate-800 px-5 py-4"
        style={{ borderLeftWidth: 3, borderLeftColor: color }}
      >
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[10px] text-slate-600 uppercase tracking-widest mb-1">
            File Detail
          </p>
          <p className="font-mono text-sm font-semibold text-slate-200 truncate">
            {file.path}
          </p>
        </div>
        <span
          className={`mt-1 shrink-0 rounded border px-2 py-0.5 font-mono text-[10px] font-bold ${getRiskBg(file.riskLevel)}`}
        >
          {getRiskLabel(file.riskLevel)}
        </span>
      </div>

      {/* Metrics */}
      <div className="px-5 pt-2">
        <MetricRow
          label="Risk Score"
          value={file.riskScore}
          color={color}
        />
        <MetricRow label="Cyclomatic Complexity" value={file.complexity} highlight />
        <MetricRow label="Lines of Code" value={file.lines.toLocaleString()} />
        <MetricRow label="Longest Function" value={`${file.longestFunction} lines`} />
        <MetricRow
          label="Ruff Issues"
          value={file.ruffIssues}
          color={file.ruffIssues > 0 ? "#f97316" : "#22c55e"}
        />
        <MetricRow
          label="TODO / FIXME"
          value={file.todoCount}
          color={file.todoCount > 0 ? "#eab308" : "#475569"}
        />
      </div>

      {/* Risk score bar */}
      <div className="px-5 py-3">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${file.riskScore}%`, backgroundColor: color }}
          />
        </div>
      </div>

      {/* Reasons */}
      <div className="border-t border-slate-800 px-5 py-4">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
          Why it&apos;s risky
        </p>
        <ul className="flex flex-col gap-2">
          {file.reasons.map((reason, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="mt-0.5 shrink-0 text-sky-500">›</span>
              <span className="text-xs text-slate-400">{reason}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
