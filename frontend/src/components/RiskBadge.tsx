import { type RiskLevel, getRiskBg, getRiskLabel } from "@/lib/mockData";

interface RiskBadgeProps {
  level: RiskLevel;
  size?: "sm" | "md";
}

export default function RiskBadge({ level, size = "sm" }: RiskBadgeProps) {
  const sizeClass = size === "md"
    ? "px-2.5 py-1 text-xs"
    : "px-1.5 py-0.5 text-[10px]";

  return (
    <span
      className={`inline-block shrink-0 rounded border font-mono font-semibold ${sizeClass} ${getRiskBg(level)}`}
    >
      {getRiskLabel(level)}
    </span>
  );
}
