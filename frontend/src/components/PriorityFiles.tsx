import type { FileRecord } from "@/lib/mockData";
import { scoreToLevel, getRiskColor, getRiskLabel } from "@/lib/mockData";
import RiskBadge from "./RiskBadge";

interface PriorityFilesProps {
  files: FileRecord[];
  onSelect: (file: FileRecord) => void;
  selectedId: string | null;
}

export default function PriorityFiles({ files, onSelect, selectedId }: PriorityFilesProps) {
  // Sort by risk_score descending and take top 7
  const sorted = [...files].sort((a, b) => b.risk_score - a.risk_score).slice(0, 7);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          Priority Targets
        </h2>
        <span className="font-mono text-xs text-slate-600">
          Top {sorted.length} by risk score
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {sorted.map((file, idx) => {
          const isSelected = selectedId === file.id;
          const level = scoreToLevel(file.risk_score);
          const color = getRiskColor(level);
          const issueCount = file.issues.duplicates.length + file.issues.dead_code.length;

          return (
            <button
              key={file.id}
              onClick={() => onSelect(file)}
              className={`group relative w-full rounded-lg border text-left transition ${
                isSelected
                  ? "border-indigo-500/40 bg-indigo-500/5"
                  : "border-slate-700/50 bg-slate-900/50 hover:border-slate-600/60 hover:bg-slate-800/60"
              }`}
            >
              {/* Risk bar fill at bottom */}
              <div
                className="absolute bottom-0 left-0 h-0.5 rounded-b-lg transition-all duration-500"
                style={{ width: `${file.risk_score}%`, backgroundColor: color, opacity: 0.6 }}
              />

              <div className="flex items-center gap-3 px-4 py-3">
                {/* Rank number */}
                <span className="w-5 shrink-0 font-mono text-xs text-slate-600">
                  {String(idx + 1).padStart(2, "0")}
                </span>

                {/* File path */}
                <span className="min-w-0 flex-1 truncate font-mono text-xs text-slate-300 group-hover:text-slate-200">
                  {file.file_path}
                </span>

                {/* Issue count */}
                {issueCount > 0 && (
                  <span className="shrink-0 font-mono text-[10px] text-slate-600 hidden sm:inline">
                    {issueCount} issue{issueCount !== 1 ? "s" : ""}
                  </span>
                )}

                {/* Risk score */}
                <span className="shrink-0 font-mono text-sm font-bold w-8 text-right" style={{ color }}>
                  {file.risk_score.toFixed(0)}
                </span>

                {/* Badge */}
                <RiskBadge level={level} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
