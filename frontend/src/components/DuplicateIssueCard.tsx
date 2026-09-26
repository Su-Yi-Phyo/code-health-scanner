import type { DuplicateIssue } from "@/lib/mockData";

interface DuplicateIssueCardProps {
  issue: DuplicateIssue;
}

export default function DuplicateIssueCard({ issue }: DuplicateIssueCardProps) {
  return (
    <div className="rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-3">
      <div className="flex items-center gap-2 mb-2">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#facc15" strokeWidth="2.5" className="shrink-0">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
        <span className="font-mono text-[10px] font-semibold uppercase tracking-widest text-yellow-400">
          Duplicate Code
        </span>
      </div>
      <p className="font-mono text-xs text-slate-300 mb-1">
        Lines {issue.line_start}–{issue.line_end}
      </p>
      <p className="font-mono text-[11px] text-slate-500">
        Duplicates:{" "}
        <span className="text-yellow-400/80">{issue.duplicate_of}</span>
      </p>
    </div>
  );
}
