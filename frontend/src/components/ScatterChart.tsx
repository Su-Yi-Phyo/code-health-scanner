"use client";

import type { FileRecord } from "@/lib/mockData";
import { getRiskColor } from "@/lib/mockData";

interface ScatterChartProps {
  files: FileRecord[];
  onSelect: (file: FileRecord) => void;
  selectedId: string | null;
}

export default function ScatterChart({ files, onSelect, selectedId }: ScatterChartProps) {
  const maxLines = Math.max(...files.map((f) => f.lines)) * 1.1;
  const maxComplexity = Math.max(...files.map((f) => f.complexity)) * 1.1;

  const CHART_W = 420;
  const CHART_H = 220;
  const PAD_LEFT = 44;
  const PAD_BOTTOM = 32;
  const PAD_TOP = 12;
  const PAD_RIGHT = 16;

  const plotW = CHART_W - PAD_LEFT - PAD_RIGHT;
  const plotH = CHART_H - PAD_BOTTOM - PAD_TOP;

  function toX(lines: number) {
    return PAD_LEFT + (lines / maxLines) * plotW;
  }
  function toY(complexity: number) {
    return PAD_TOP + plotH - (complexity / maxComplexity) * plotH;
  }

  // Grid lines
  const xTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    val: Math.round(t * maxLines),
    x: PAD_LEFT + t * plotW,
  }));
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    val: Math.round(t * maxComplexity),
    y: PAD_TOP + plotH - t * plotH,
  }));

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
          Complexity vs Lines
        </h2>
        <span className="font-mono text-xs text-slate-600">
          X: lines · Y: complexity
        </span>
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-5">
        <div className="w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${CHART_W} ${CHART_H}`}
            className="w-full"
            style={{ minWidth: 280 }}
          >
            {/* Grid lines */}
            {xTicks.map((t) => (
              <line
                key={`gx-${t.val}`}
                x1={t.x} y1={PAD_TOP}
                x2={t.x} y2={PAD_TOP + plotH}
                stroke="#1e293b" strokeWidth="1"
              />
            ))}
            {yTicks.map((t) => (
              <line
                key={`gy-${t.val}`}
                x1={PAD_LEFT} y1={t.y}
                x2={PAD_LEFT + plotW} y2={t.y}
                stroke="#1e293b" strokeWidth="1"
              />
            ))}

            {/* Axes */}
            <line x1={PAD_LEFT} y1={PAD_TOP} x2={PAD_LEFT} y2={PAD_TOP + plotH} stroke="#334155" strokeWidth="1" />
            <line x1={PAD_LEFT} y1={PAD_TOP + plotH} x2={PAD_LEFT + plotW} y2={PAD_TOP + plotH} stroke="#334155" strokeWidth="1" />

            {/* X-axis labels */}
            {xTicks.map((t) => (
              <text
                key={`xl-${t.val}`}
                x={t.x} y={CHART_H - 6}
                textAnchor="middle"
                className="font-mono"
                fill="#475569" fontSize="9"
              >
                {t.val}
              </text>
            ))}

            {/* Y-axis labels */}
            {yTicks.map((t) => (
              <text
                key={`yl-${t.val}`}
                x={PAD_LEFT - 6} y={t.y + 3}
                textAnchor="end"
                className="font-mono"
                fill="#475569" fontSize="9"
              >
                {t.val}
              </text>
            ))}

            {/* Data points */}
            {files.map((file) => {
              const cx = toX(file.lines);
              const cy = toY(file.complexity);
              const color = getRiskColor(file.riskLevel);
              const isSelected = selectedId === file.id;
              const r = 5 + (file.riskScore / 100) * 4;

              return (
                <g key={file.id} onClick={() => onSelect(file)} style={{ cursor: "pointer" }}>
                  {/* Outer ring on selected */}
                  {isSelected && (
                    <circle
                      cx={cx} cy={cy} r={r + 4}
                      fill="none"
                      stroke={color} strokeWidth="1.5" opacity="0.5"
                    />
                  )}
                  <circle
                    cx={cx} cy={cy} r={r}
                    fill={color}
                    fillOpacity={isSelected ? 0.9 : 0.6}
                    stroke={color}
                    strokeWidth="1"
                  />
                  {/* Hover tooltip via title */}
                  <title>{`${file.path}\nScore: ${file.riskScore} · Complexity: ${file.complexity} · Lines: ${file.lines}`}</title>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap gap-4 border-t border-slate-800 pt-3">
          {[
            { label: "Critical (≥75)", color: "#ef4444" },
            { label: "High (≥50)", color: "#f97316" },
            { label: "Medium (≥25)", color: "#eab308" },
            { label: "Low (<25)", color: "#22c55e" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="font-mono text-[10px] text-slate-500">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
