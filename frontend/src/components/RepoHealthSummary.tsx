import type { RepoSummary } from "@/lib/mockData";

interface RepoHealthSummaryProps {
  summary: RepoSummary;
}

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}

function StatCard({ label, value, sub, accent = "text-sky-400" }: StatCardProps) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-slate-900/60 p-5 transition hover:border-slate-600/60">
      <p className="text-xs font-medium uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`mt-2 font-mono text-3xl font-bold ${accent}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

export default function RepoHealthSummary({ summary }: RepoHealthSummaryProps) {
  const avgRiskAccent =
    summary.avgRiskScore >= 60
      ? "text-red-400"
      : summary.avgRiskScore >= 35
      ? "text-yellow-400"
      : "text-green-400";

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <span className="h-px flex-1 bg-slate-800" />
        <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">
          Repository Health Summary
        </h2>
        <span className="h-px flex-1 bg-slate-800" />
      </div>

      {/* Repo URL breadcrumb */}
      <p className="mb-5 font-mono text-sm text-slate-500 truncate">
        <span className="text-sky-500">▸</span>{" "}
        <a
          href={summary.repoUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-sky-400 transition"
        >
          {summary.repoUrl}
        </a>
      </p>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Python Files"
          value={summary.fileCount}
          sub="files scanned"
        />
        <StatCard
          label="Total Lines"
          value={summary.totalLines.toLocaleString()}
          sub="lines of code"
        />
        <StatCard
          label="Avg Risk Score"
          value={summary.avgRiskScore}
          sub="out of 100"
          accent={avgRiskAccent}
        />
        <StatCard
          label="High-Risk Files"
          value={summary.highRiskCount}
          sub="need attention"
          accent="text-red-400"
        />
      </div>
    </div>
  );
}
