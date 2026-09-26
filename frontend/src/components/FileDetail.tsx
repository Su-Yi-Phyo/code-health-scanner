"use client";

import { useState } from "react";
import type { FileRecord } from "@/lib/mockData";
import { scoreToLevel, getRiskColor } from "@/lib/mockData";
import RiskBadge from "./RiskBadge";
import DuplicateIssueCard from "./DuplicateIssueCard";
import DeadCodeIssueCard from "./DeadCodeIssueCard";

interface FileDetailProps {
  file: FileRecord | null;
}

// Language display names and color dots
const LANG_COLORS: Record<string, string> = {
  Python:     "#3b82f6",
  TypeScript: "#6366f1",
  JavaScript: "#eab308",
  Go:         "#06b6d4",
  Java:       "#f97316",
  Rust:       "#f59e0b",
  YAML:       "#22c55e",
  default:    "#94a3b8",
};

function langColor(lang: string): string {
  return LANG_COLORS[lang] ?? LANG_COLORS.default;
}

const INITIAL_SHOWN = 5;

interface IssueListProps {
  label: string;
  count: number;
  children: React.ReactNode;
}

function CollapsibleIssueList({ label, count, children }: IssueListProps) {
  const [expanded, setExpanded] = useState(false);
  const items = Array.isArray(children)
    ? (children as React.ReactNode[])
    : [children];
  const visible = expanded ? items : items.slice(0, INITIAL_SHOWN);

  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-2">
        {label} ({count})
      </p>
      <div className="flex flex-col gap-2">{visible}</div>
      {count > INITIAL_SHOWN && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-2 w-full rounded-md border border-slate-700/50 py-1.5 font-mono text-[11px] text-slate-500 transition hover:border-slate-600 hover:text-slate-300"
        >
          {expanded
            ? "Show less"
            : `Show all ${count} issues \u25be`}
        </button>
      )}
    </div>
  );
}

export default function FileDetail({ file }: FileDetailProps) {
  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-slate-700/50 bg-slate-900/30 p-12 text-center h-full min-h-[200px]">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-700">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        <div>
          <p className="text-sm font-medium text-slate-500 mb-1">No file selected</p>
          <p className="text-xs text-slate-700">
            Click a file in the explorer or priority list to view its analysis.
          </p>
        </div>
      </div>
    );
  }

  const level = scoreToLevel(file.risk_score);
  const color = getRiskColor(level);
  const hasIssues = file.issues.duplicates.length > 0 || file.issues.dead_code.length > 0;

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 overflow-hidden">
      {/* Header — accent left border */}
      <div
        className="px-5 py-4 border-b border-slate-800"
        style={{ borderLeftWidth: 3, borderLeftColor: color }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-1">
              File Analysis
            </p>
            <p className="font-mono text-sm font-semibold text-slate-200 break-all">
              {file.file_path}
            </p>
          </div>
          <RiskBadge level={level} size="md" />
        </div>
      </div>

      {/* Metrics */}
      <div className="px-5 py-4 grid grid-cols-2 gap-x-4 gap-y-3 border-b border-slate-800">
        {/* Risk score */}
        <div className="col-span-2">
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-1">Risk Score</p>
          <div className="flex items-center gap-3">
            <span className="font-mono text-4xl font-bold" style={{ color }}>
              {file.risk_score.toFixed(0)}
            </span>
            <div className="flex-1">
              <p className="font-mono text-[10px] text-slate-600 mb-1">/ 100</p>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${file.risk_score}%`, backgroundColor: color }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Language */}
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-1">Language</p>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full shrink-0"
              style={{ backgroundColor: langColor(file.language) }}
            />
            <span className="font-mono text-sm text-slate-300">{file.language}</span>
          </div>
        </div>

        {/* Lines */}
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-1">Lines of Code</p>
          <span className="font-mono text-sm text-slate-300">{file.line_count.toLocaleString()}</span>
        </div>

        {/* Duplicate issues */}
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-1">Duplicate Code</p>
          <span className={`font-mono text-sm font-semibold ${file.issues.duplicates.length > 0 ? "text-yellow-400" : "text-slate-600"}`}>
            {file.issues.duplicates.length} instance{file.issues.duplicates.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Dead code issues */}
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-600 mb-1">Dead Code</p>
          <span className={`font-mono text-sm font-semibold ${file.issues.dead_code.length > 0 ? "text-orange-400" : "text-slate-600"}`}>
            {file.issues.dead_code.length} instance{file.issues.dead_code.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Issue details */}
      <div className="px-5 py-4">
        {!hasIssues ? (
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-green-500/20 bg-green-500/5 py-6 text-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <p className="text-sm font-medium text-green-400">All Clear</p>
            <p className="text-xs text-slate-500">No duplicate or dead-code issues detected in this file.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {/* Duplicate issues */}
            {file.issues.duplicates.length > 0 && (
              <CollapsibleIssueList
                label="Duplicate Code Issues"
                count={file.issues.duplicates.length}
              >
                {file.issues.duplicates.map((issue, i) => (
                  <DuplicateIssueCard key={i} issue={issue} />
                ))}
              </CollapsibleIssueList>
            )}

            {/* Dead code issues */}
            {file.issues.dead_code.length > 0 && (
              <CollapsibleIssueList
                label="Dead Code Issues"
                count={file.issues.dead_code.length}
              >
                {file.issues.dead_code.map((issue, i) => (
                  <DeadCodeIssueCard key={i} issue={issue} />
                ))}
              </CollapsibleIssueList>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
