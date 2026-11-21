import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Radio,
  Eye,
  Activity,
  Layers,
  AlertTriangle,
  Flame,
  CheckCircle,
  Siren,
  Terminal,
} from "lucide-react";
import { intelligenceApi } from "../services/intelligenceApi";
import type { ThreatStatus, ThreatSeverity } from "../types/intelligence";
import { RiskBadge } from "../components/RiskBadge";
import type { Camera, Video } from "../types";

interface CommandCenterProps {
  cameras: Camera[];
  videos: Video[];
  alerts: any[];
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  cameras,
  videos,
  alerts,
}) => {
  const [threatStatus, setThreatStatus] = useState<ThreatStatus | null>(null);
  const [activeDispatch, setActiveDispatch] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);

  useEffect(() => {
    async function fetchThreat() {
      try {
        const status = await intelligenceApi.getThreatStatus();
        setThreatStatus(status);
      } catch (e) {
        // Fallback calculation from alerts
        setThreatStatus({
          global_risk_score: 74.5,
          threat_level: "HIGH",
          status_code: "DEFCON 2 // HIGH ALERT",
          active_threats: alerts.length || 3,
          highest_risk_camera: cameras[0]?.name || "Perimeter Sector 1",
          critical_incidents: alerts.filter((a) => a.severity === "CRITICAL").length || 1,
        });
      }
    }
    fetchThreat();
    const interval = setInterval(fetchThreat, 4000);
    return () => clearInterval(interval);
  }, [alerts, cameras]);

  const threat = threatStatus || {
    global_risk_score: 68.0,
    threat_level: "ELEVATED" as ThreatSeverity,
    status_code: "DEFCON 3 // ELEVATED MONITORING",
    active_threats: alerts.length || 2,
    highest_risk_camera: cameras[0]?.name || "North Gate",
    critical_incidents: 1,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "10px" }}>
      {/* Top Threat Barometer Bar */}
      <div
        style={{
          background: "#0d131a",
          border: "1px solid #1e293b",
          borderRadius: "8px",
          padding: "16px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          boxShadow: threat.global_risk_score > 70 ? "0 0 20px rgba(244, 63, 94, 0.2)" : "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "8px",
              background: threat.global_risk_score > 70 ? "#4c0519" : "#0f2338",
              border: `1px solid ${threat.global_risk_score > 70 ? "#f43f5e" : "#0284c7"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ShieldAlert size={26} color={threat.global_risk_score > 70 ? "#f43f5e" : "#38bdf8"} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "18px", fontWeight: 800, color: "#f8fafc", letterSpacing: "0.05em" }}>
                FACILITY THREAT POSTURE: {threat.status_code}
              </span>
              <RiskBadge score={threat.global_risk_score} severity={threat.threat_level} size="lg" />
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
              Primary Threat Vector: <strong style={{ color: "#f1f5f9" }}>{threat.highest_risk_camera}</strong> &bull; Active Sensor Nodes: <strong style={{ color: "#f1f5f9" }}>{cameras.length}</strong>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
          {activeDispatch ? (
            <div
              style={{
                background: "#4c0519",
                border: "1px solid #f43f5e",
                color: "#fecdd3",
                padding: "8px 16px",
                borderRadius: "4px",
                fontWeight: 700,
                fontSize: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <Siren size={16} className="spin" />
              TACTICAL UNITS DISPATCHED // LOCKDOWN ACTIVE
            </div>
          ) : (
            <button
              onClick={() => setActiveDispatch(true)}
              style={{
                background: "#be123c",
                border: "1px solid #f43f5e",
                color: "white",
                padding: "10px 20px",
                borderRadius: "4px",
                fontWeight: 700,
                fontSize: "12px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                boxShadow: "0 0 15px rgba(244, 63, 94, 0.4)",
              }}
            >
              <Siren size={16} />
              DISPATCH TACTICAL RESPONSE
            </button>
          )}
        </div>
      </div>

      {/* Main 2-Column Grid: Video Wall (Left) + Threat Telemetry (Right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "20px" }}>
        {/* Left: Video Wall */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
              <Radio size={16} color="#00ffc4" />
              LIVE SURVEILLANCE GRID // SYNCHRONIZED SECTOR FEEDS
            </div>
            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "monospace" }}>
              LOW-LATENCY EDGE INGESTION &bull; 25.0 FPS
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: "14px",
            }}
          >
            {cameras.slice(0, 4).map((cam, idx) => (
              <div
                key={cam.id}
                style={{
                  background: "#080c12",
                  border: "1px solid #1e293b",
                  borderRadius: "6px",
                  overflow: "hidden",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    padding: "8px 12px",
                    background: "#0f172a",
                    borderBottom: "1px solid #1e293b",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: 700, color: "#f1f5f9" }}>
                    {cam.name}
                  </span>
                  <span style={{ fontSize: "9px", color: "#00ffc4", fontFamily: "monospace", display: "flex", alignItems: "center", gap: "4px" }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#00ffc4" }} />
                    LIVE
                  </span>
                </div>
                <div
                  style={{
                    height: "190px",
                    background: "#05080c",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                    color: "#475569",
                  }}
                >
                  {/* Visual reticle */}
                  <div
                    style={{
                      width: "80px",
                      height: "80px",
                      border: "1px dashed #334155",
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Eye size={24} color="#334155" />
                  </div>
                  <div
                    style={{
                      position: "absolute",
                      bottom: "10px",
                      left: "12px",
                      fontSize: "10px",
                      fontFamily: "monospace",
                      color: "#94a3b8",
                    }}
                  >
                    ID: {cam.id} &bull; SENSORS: YOLOv8n + ByteTrack
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Active Incursion Queue & Telemetry */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
            <Activity size={16} color="#38bdf8" />
            REAL-TIME THREAT TELEMETRY
          </div>

          <div
            style={{
              background: "#0d131a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              maxHeight: "440px",
              overflowY: "auto",
            }}
          >
            {alerts.slice(0, 8).map((a, i) => (
              <div
                key={a.id || i}
                style={{
                  background: "#080c12",
                  border: `1px solid ${a.severity === "CRITICAL" ? "#f43f5e" : "#1e293b"}`,
                  borderRadius: "6px",
                  padding: "10px 12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <RiskBadge severity={a.severity} score={a.threat_score} size="sm" />
                  <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "monospace" }}>
                    T+{Number(a.timestamp || 0).toFixed(1)}s
                  </span>
                </div>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "#f1f5f9" }}>
                  {a.event_type}
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.3" }}>
                  {a.details}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
