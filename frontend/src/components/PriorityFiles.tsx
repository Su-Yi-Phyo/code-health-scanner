import type { FileRecord } from "@/lib/mockData";
import { getRiskBg, getRiskColor, getRiskLabel } from "@/lib/mockData";

interface PriorityFilesProps {
  files: FileRecord[];
  onSelect: (file: FileRecord) => void;
  selectedId: string | null;
}

export default function PriorityFiles({
  files,
  onSelect,
  selectedId,
}: PriorityFilesProps) {
  const top5 = files.slice(0, 5);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          Priority Files
        </h2>
        <span className="font-mono text-xs text-slate-600">
          Top {top5.length} by risk
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {top5.map((file, idx) => {
          const isSelected = selectedId === file.id;
          const barWidth = `${file.riskScore}%`;
          const color = getRiskColor(file.riskLevel);

          return (
            <button
              key={file.id}
              onClick={() => onSelect(file)}
              className={`group relative w-full rounded-lg border text-left transition ${
                isSelected
                  ? "border-sky-500/40 bg-sky-500/5"
                  : "border-slate-700/50 bg-slate-900/50 hover:border-slate-600/60 hover:bg-slate-800/60"
              }`}
            >
              {/* Risk bar fill */}
              <div
                className="absolute bottom-0 left-0 h-0.5 rounded-b-lg transition-all duration-500"
                style={{
                  width: barWidth,
                  backgroundColor: color,
                  opacity: 0.5,
                }}
              />

              <div className="flex items-center gap-3 px-4 py-3">
                {/* Rank */}
                <span className="w-5 shrink-0 font-mono text-xs text-slate-600">
                  {String(idx + 1).padStart(2, "0")}
                </span>

                {/* File path */}
                <span className="min-w-0 flex-1 truncate font-mono text-xs text-slate-300 group-hover:text-slate-200">
                  {file.path}
                </span>

                {/* Risk score */}
                <span
                  className="shrink-0 font-mono text-sm font-bold"
                  style={{ color }}
                >
                  {file.riskScore}
                </span>

                {/* Badge */}
                <span
                  className={`shrink-0 rounded border px-1.5 py-0.5 font-mono text-[10px] font-semibold ${getRiskBg(file.riskLevel)}`}
                >
                  {getRiskLabel(file.riskLevel)}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
