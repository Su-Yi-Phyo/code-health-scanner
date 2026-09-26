import type { DuplicateIssue } from "@/lib/mockData";

interface DuplicateIssueCardProps {
  issue: DuplicateIssue;
}

/**
 * Strip Windows/Unix temp-directory prefixes from backend-generated paths
 * so users see clean, repo-relative paths instead of system temp paths.
 *
 * Examples that get cleaned:
 *   C:\Users\...\AppData\Local\Temp\code_health_abc123\repo\src\foo.py
 *   /tmp/code_health_abc123/repo/src/foo.py
 *
 * The heuristic: find the last occurrence of a segment that looks like
 * a temp-clone root (e.g. "code_health_*" or a hex/uuid-style temp dir)
 * and take everything after it.  If no known temp segment is found we fall
 * back to normalising backslashes only so nothing is lost.
 */
function cleanDuplicatePath(raw: string): string {
  // Normalise backslashes first
  const path = raw.replace(/\\/g, "/");

  // Known temp-dir patterns produced by the CodePulse backend
  const tempPattern = /(?:\/|^)[^/]*(?:AppData\/Local\/Temp|\/[Tt]emp|code_health_[^/]+)[^/]*(?:\/[^/]+)*(\/)/;
  const match = tempPattern.exec(path);
  if (match) {
    // Return the portion after the last matched segment separator
    return path.slice(match.index + match[0].length - match[1].length + 1);
  }

  // Fallback: strip everything up to and including any recognisable temp dir.
  // Look for a segment matching code_health_<anything> and take what follows.
  const codeHealthIdx = path.indexOf("code_health_");
  if (codeHealthIdx !== -1) {
    const afterTempDir = path.indexOf("/", codeHealthIdx);
    if (afterTempDir !== -1) {
      return path.slice(afterTempDir + 1);
    }
  }

  // If no temp dir pattern found, just return the normalised path.
  return path;
}

export default function DuplicateIssueCard({ issue }: DuplicateIssueCardProps) {
  const cleanPath = cleanDuplicatePath(issue.duplicate_of);

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
        Lines {issue.line_start}&ndash;{issue.line_end}
      </p>
      <p className="font-mono text-[11px] text-slate-500 break-all">
        Duplicates:{" "}
        <span className="text-yellow-400/80">{cleanPath}</span>
      </p>
    </div>
  );
}
