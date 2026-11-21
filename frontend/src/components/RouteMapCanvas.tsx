import React from "react";
import type { RouteNode } from "../types/intelligence";
import { RiskBadge } from "./RiskBadge";
import { Clock, ShieldAlert, ArrowRight, Video } from "lucide-react";

interface RouteMapCanvasProps {
  route: RouteNode[];
  onSelectStep?: (step: RouteNode) => void;
  selectedStep?: RouteNode | null;
}

export const RouteMapCanvas: React.FC<RouteMapCanvasProps> = ({
  route,
  onSelectStep,
  selectedStep,
}) => {
  if (!route || route.length === 0) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
        No multi-camera route transitions detected for this target.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", overflowX: "auto", padding: "10px 0" }}>
      {/* Node Trajectory Flow */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          minWidth: `${route.length * 240}px`,
          padding: "20px 10px",
        }}
      >
        {route.map((step, idx) => {
          const isSelected = selectedStep?.step_order === step.step_order;
          return (
            <React.Fragment key={step.step_order}>
              <div
                onClick={() => onSelectStep && onSelectStep(step)}
                style={{
                  flex: "0 0 220px",
                  background: isSelected ? "#1e293b" : "#0f172a",
                  border: isSelected ? "2px solid #38bdf8" : "1px solid #334155",
                  borderRadius: "8px",
                  padding: "14px",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  boxShadow: isSelected ? "0 0 15px rgba(56, 189, 248, 0.25)" : "none",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span
                    style={{
                      background: "#334155",
                      color: "#94a3b8",
                      fontSize: "10px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      fontWeight: "bold",
                    }}
                  >
                    PHASE #{step.step_order}
                  </span>
                  <RiskBadge score={step.risk_score} size="sm" />
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 700, fontSize: "13px", color: "#f8fafc", marginBottom: "6px" }}>
                  <Video size={14} color="#38bdf8" />
                  <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {step.camera_name}
                  </span>
                </div>

                <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", alignItems: "center", gap: "5px", marginBottom: "8px" }}>
                  <Clock size={12} />
                  <span>T+{step.entry_time.toFixed(1)}s &rarr; T+{step.exit_time.toFixed(1)}s ({step.dwell_seconds}s)</span>
                </div>

                <div
                  style={{
                    fontSize: "11px",
                    background: "#182234",
                    color: "#cbd5e1",
                    padding: "6px 8px",
                    borderRadius: "4px",
                    lineHeight: "1.3",
                  }}
                >
                  {step.action}
                </div>
              </div>

              {idx < route.length - 1 && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", color: "#38bdf8" }}>
                  <ArrowRight size={20} />
                  <span style={{ fontSize: "9px", color: "#64748b", fontFamily: "monospace" }}>TRANSIT</span>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
