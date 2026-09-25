import type { FileRecord } from "@/lib/mockData";
import { getRiskColor } from "@/lib/mockData";

interface RiskBarChartProps {
  files: FileRecord[];
  onSelect: (file: FileRecord) => void;
  selectedId: string | null;
}

export default function RiskBarChart({ files, onSelect, selectedId }: RiskBarChartProps) {
  const maxScore = 100;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          Top 10 Risky Files
        </h2>
        <span className="font-mono text-xs text-slate-600">Risk Score / 100</span>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-5">
        {/* Y-axis labels and chart area */}
        <div className="flex flex-col gap-2">
          {files.map((file) => {
            const pct = (file.riskScore / maxScore) * 100;
            const color = getRiskColor(file.riskLevel);
            const isSelected = selectedId === file.id;
            const shortName = file.path.split("/").pop() ?? file.path;

            return (
              <button
                key={file.id}
                onClick={() => onSelect(file)}
                className={`group flex w-full items-center gap-3 rounded-md px-2 py-1.5 text-left transition ${
                  isSelected ? "bg-sky-500/5" : "hover:bg-slate-800/60"
                }`}
              >
                {/* File label */}
                <span className="w-40 shrink-0 truncate font-mono text-xs text-slate-400 group-hover:text-slate-200">
                  {shortName}
                </span>

                {/* Bar track */}
                <div className="relative flex-1 overflow-hidden rounded-full bg-slate-800" style={{ height: "6px" }}>
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: color,
                      opacity: isSelected ? 1 : 0.7,
                    }}
                  />
                </div>

                {/* Score */}
                <span
                  className="w-8 shrink-0 text-right font-mono text-xs font-bold"
                  style={{ color }}
                >
                  {file.riskScore}
                </span>
              </button>
            );
          })}
        </div>

        {/* X-axis ticks */}
        <div className="mt-3 flex justify-between border-t border-slate-800 pt-2">
          {[0, 25, 50, 75, 100].map((v) => (
            <span key={v} className="font-mono text-[10px] text-slate-700">{v}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
