import type { FileRecord } from "@/lib/mockData";
import { getRiskBg, getRiskColor, getRiskLabel } from "@/lib/mockData";

interface FileTableProps {
  files: FileRecord[];
  onSelect: (file: FileRecord) => void;
  selectedId: string | null;
}

const COLS = [
  { key: "path",      label: "File Path",   align: "left"  },
  { key: "riskScore", label: "Risk",        align: "right" },
  { key: "complexity",label: "Complexity",  align: "right" },
  { key: "lines",     label: "Lines",       align: "right" },
  { key: "ruffIssues",label: "Ruff",        align: "right" },
  { key: "status",    label: "Status",      align: "center"},
] as const;

export default function FileTable({ files, onSelect, selectedId }: FileTableProps) {
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          File Rankings
        </h2>
        <span className="font-mono text-xs text-slate-600">{files.length} files</span>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-700/50">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80">
                {COLS.map((col) => (
                  <th
                    key={col.key}
                    className={`px-4 py-3 font-mono text-[10px] font-semibold uppercase tracking-widest text-slate-600 ${
                      col.align === "right"  ? "text-right"  :
                      col.align === "center" ? "text-center" : "text-left"
                    }`}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {files.map((file, idx) => {
                const isSelected = selectedId === file.id;
                const color = getRiskColor(file.riskLevel);
                const isEven = idx % 2 === 0;

                return (
                  <tr
                    key={file.id}
                    onClick={() => onSelect(file)}
                    className={`cursor-pointer border-b border-slate-800/60 transition ${
                      isSelected
                        ? "bg-sky-500/5"
                        : isEven
                        ? "bg-slate-900/40 hover:bg-slate-800/50"
                        : "bg-slate-900/20 hover:bg-slate-800/50"
                    }`}
                  >
                    {/* File path */}
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-slate-300">
                        {file.path}
                      </span>
                    </td>

                    {/* Risk score with mini bar */}
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-1 w-12 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${file.riskScore}%`,
                              backgroundColor: color,
                            }}
                          />
                        </div>
                        <span
                          className="w-6 font-mono text-xs font-bold"
                          style={{ color }}
                        >
                          {file.riskScore}
                        </span>
                      </div>
                    </td>

                    {/* Complexity */}
                    <td className="px-4 py-3 text-right font-mono text-xs text-slate-400">
                      {file.complexity}
                    </td>

                    {/* Lines */}
                    <td className="px-4 py-3 text-right font-mono text-xs text-slate-400">
                      {file.lines.toLocaleString()}
                    </td>

                    {/* Ruff issues */}
                    <td className="px-4 py-3 text-right font-mono text-xs">
                      <span className={file.ruffIssues > 0 ? "text-orange-400" : "text-slate-600"}>
                        {file.ruffIssues}
                      </span>
                    </td>

                    {/* Status badge */}
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-block rounded border px-1.5 py-0.5 font-mono text-[10px] font-semibold ${getRiskBg(file.riskLevel)}`}
                      >
                        {getRiskLabel(file.riskLevel)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
