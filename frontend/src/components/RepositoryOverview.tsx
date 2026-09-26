import type { ScanResult } from "@/lib/mockData";
import { scoreToLevel, getRiskColor, getRiskBg, getRiskLabel } from "@/lib/mockData";

interface RepositoryOverviewProps {
  result: ScanResult;
}

function riskyFileCount(result: ScanResult): number {
  return result.files.filter((f) => f.risk_score > 50).length;
}

export default function RepositoryOverview({ result }: RepositoryOverviewProps) {
  const level = scoreToLevel(result.repositoryScore);
  const color = getRiskColor(level);
  const folderCount = Object.keys(result.folderScores).length;
  const risky = riskyFileCount(result);

  // Extract repo name from URL
  const repoName = result.repositoryUrl.replace("https://github.com/", "");

  return (
    <div>
      {/* Section header */}
      <div className="mb-6 flex items-center gap-3">
        <span className="h-px flex-1 bg-slate-800" />
        <h2 className="font-mono text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          Repository Pulse
        </h2>
        <span className="h-px flex-1 bg-slate-800" />
      </div>

      {/* Repo URL */}
      <div className="mb-6 flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 text-indigo-400">
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
        </svg>
        <a
          href={result.repositoryUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-sm text-slate-300 transition hover:text-indigo-400 truncate"
        >
          {repoName}
        </a>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-4">

        {/* Risk score — prominent card */}
        <div
          className="relative overflow-hidden rounded-xl border bg-slate-900/60 p-5 md:col-span-1"
          style={{ borderColor: `${color}30` }}
        >
          <div
            className="pointer-events-none absolute inset-0 opacity-5"
            style={{ background: `radial-gradient(ellipse at 50% 100%, ${color}, transparent 70%)` }}
          />
          <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-2">
            Repository Score
          </p>
          <p className="font-mono text-5xl font-bold leading-none" style={{ color }}>
            {result.repositoryScore.toFixed(1)}
          </p>
          <p className="font-mono text-xs text-slate-600 mt-1">/ 100</p>
          <div className="mt-3">
            <span className={`inline-block rounded border px-2 py-0.5 font-mono text-[10px] font-bold ${getRiskBg(level)}`}>
              {getRiskLabel(level)}
            </span>
          </div>
          {/* Mini progress bar */}
          <div className="mt-4 h-1 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${result.repositoryScore}%`, backgroundColor: color }}
            />
          </div>
        </div>

        {/* Stats grid */}
        <div className="md:col-span-3 grid grid-cols-3 gap-4">
          <StatCard
            label="Files Analyzed"
            value={result.fileCount}
            sub="total files scanned"
          />
          <StatCard
            label="Folders"
            value={folderCount}
            sub="directories tracked"
          />
          <StatCard
            label="Risky Files"
            value={risky}
            sub="score > 50"
            accent="text-orange-400"
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  accent = "text-indigo-400",
}: {
  label: string;
  value: number;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-slate-900/60 p-5 transition hover:border-slate-600/60">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`mt-2 font-mono text-3xl font-bold ${accent}`}>{value}</p>
      {sub && <p className="mt-1 font-mono text-[11px] text-slate-600">{sub}</p>}
    </div>
  );
}
