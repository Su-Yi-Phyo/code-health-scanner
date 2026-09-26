// CodePulse — Shared risk helpers and type re-exports.
//
// Types are now defined in @/lib/api.ts (the single source of truth for the
// backend contract).  Components that already import from here continue to
// work unchanged because we re-export everything they need.

// ─── Re-export backend types so existing component imports keep working ───────
export type {
  DuplicateIssue,
  DeadCodeIssue,
  FileIssues,
  FileRecord,
  ScanResult,
} from "@/lib/api";

// ─── Risk helpers ────────────────────────────────────────────────────────────

export type RiskLevel = "clean" | "low" | "moderate" | "high" | "critical";

/** Map a numeric risk score (0–100) to a RiskLevel label. */
export function scoreToLevel(score: number): RiskLevel {
  if (score === 0)  return "clean";
  if (score <= 20)  return "low";
  if (score <= 50)  return "moderate";
  if (score <= 80)  return "high";
  return "critical";
}

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case "clean":    return "#22c55e";
    case "low":      return "#4ade80";
    case "moderate": return "#facc15";
    case "high":     return "#f97316";
    case "critical": return "#ef4444";
  }
}

export function getRiskBg(level: RiskLevel): string {
  switch (level) {
    case "clean":    return "bg-green-500/10 text-green-400 border-green-500/20";
    case "low":      return "bg-green-500/10 text-green-400 border-green-500/20";
    case "moderate": return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
    case "high":     return "bg-orange-500/10 text-orange-400 border-orange-500/20";
    case "critical": return "bg-red-500/10 text-red-400 border-red-500/20";
  }
}

export function getRiskLabel(level: RiskLevel): string {
  switch (level) {
    case "clean":    return "CLEAN";
    case "low":      return "LOW";
    case "moderate": return "MODERATE";
    case "high":     return "HIGH";
    case "critical": return "CRITICAL";
  }
}
