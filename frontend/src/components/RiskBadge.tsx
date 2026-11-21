import React from "react";
import type { ThreatSeverity } from "../types/intelligence";

interface RiskBadgeProps {
  score?: number;
  severity?: ThreatSeverity;
  size?: "sm" | "md" | "lg";
  pulsing?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  score,
  severity,
  size = "md",
  pulsing = true,
}) => {
  const level: ThreatSeverity = severity || (
    score !== undefined
      ? score >= 80 ? "CRITICAL"
        : score >= 60 ? "HIGH"
        : score >= 40 ? "ELEVATED"
        : score >= 20 ? "GUARDED"
        : "NORMAL"
      : "NORMAL"
  );

  const colors: Record<ThreatSeverity, { bg: string; text: string; border: string; glow: string }> = {
    CRITICAL: { bg: "#4c0519", text: "#fecdd3", border: "#f43f5e", glow: "rgba(244, 63, 94, 0.4)" },
    HIGH: { bg: "#431407", text: "#ffedd5", border: "#f97316", glow: "rgba(249, 115, 22, 0.4)" },
    ELEVATED: { bg: "#422006", text: "#fef9c3", border: "#eab308", glow: "rgba(234, 179, 8, 0.3)" },
    GUARDED: { bg: "#082f49", text: "#e0f2fe", border: "#0ea5e9", glow: "rgba(14, 165, 233, 0.3)" },
    NORMAL: { bg: "#052e16", text: "#dcfce7", border: "#10b981", glow: "rgba(16, 185, 129, 0.3)" },
    LOW: { bg: "#052e16", text: "#dcfce7", border: "#10b981", glow: "rgba(16, 185, 129, 0.3)" },
  };

  const c = colors[level] || colors.NORMAL;
  const isDanger = level === "CRITICAL" || level === "HIGH";

  const padding = size === "sm" ? "2px 6px" : size === "lg" ? "6px 14px" : "4px 10px";
  const fontSize = size === "sm" ? "10px" : size === "lg" ? "13px" : "11px";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        background: c.bg,
        color: c.text,
        border: `1px solid ${c.border}`,
        borderRadius: "4px",
        padding,
        fontSize,
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        boxShadow: pulsing && isDanger ? `0 0 10px ${c.glow}` : "none",
        fontFamily: "'JetBrains Mono', monospace, sans-serif",
      }}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: c.border,
          boxShadow: `0 0 6px ${c.border}`,
        }}
      />
      {score !== undefined ? `${score.toFixed(0)}% ` : ""}
      {level}
    </span>
  );
};
