import type { DeadCodeIssue } from "@/lib/mockData";

interface DeadCodeIssueCardProps {
  issue: DeadCodeIssue;
}

export default function DeadCodeIssueCard({ issue }: DeadCodeIssueCardProps) {
  return (
    <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-3">
      <div className="flex items-center gap-2 mb-2">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#f97316" strokeWidth="2.5" className="shrink-0">
          <polyline points="4 7 4 4 20 4 20 7" />
          <line x1="9" y1="20" x2="15" y2="20" />
          <line x1="12" y1="4" x2="12" y2="20" />
          <line x1="4" y1="4" x2="20" y2="20" />
        </svg>
        <span className="font-mono text-[10px] font-semibold uppercase tracking-widest text-orange-400">
          Dead Code
        </span>
      </div>
      <p className="font-mono text-sm font-semibold text-slate-200 mb-1">
        {issue.kind === "function" ? `${issue.name}()` : issue.name}
      </p>
      <div className="flex items-center gap-3">
        <span className="font-mono text-[11px] text-slate-500 capitalize">{issue.kind}</span>
        <span className="font-mono text-[11px] text-slate-500">
          Lines {issue.line_start}–{issue.line_end}
        </span>
      </div>
    </div>
  );
}
