import React, { useState } from "react";
import {
  GitMerge,
  Search,
  Sparkles,
  MapPin,
  Clock,
  ShieldAlert,
  FileText,
  CheckCircle,
} from "lucide-react";
import { intelligenceApi } from "../services/intelligenceApi";
import type { ReconstructedRoute, RouteNode } from "../types/intelligence";
import { RouteMapCanvas } from "../components/RouteMapCanvas";
import { RiskBadge } from "../components/RiskBadge";

export const RouteReconstruction: React.FC = () => {
  const [query, setQuery] = useState("person wearing red jacket with backpack");
  const [loading, setLoading] = useState(false);
  const [routeData, setRouteData] = useState<ReconstructedRoute | null>(null);
  const [selectedStep, setSelectedStep] = useState<RouteNode | null>(null);
  const [dossierStatus, setDossierStatus] = useState<string>("");

  async function handleReconstruct() {
    if (!query.trim()) return;
    setLoading(true);
    setDossierStatus("");
    try {
      const data = await intelligenceApi.reconstructRoute({
        query,
        time_window_minutes: 60,
        min_affinity: 0.65,
      });
      setRouteData(data);
      if (data.route && data.route.length > 0) {
        setSelectedStep(data.route[0]);
      }
    } catch (e: any) {
      alert(`Route reconstruction failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateDossier() {
    if (!routeData) return;
    setDossierStatus("Compiling certified forensic case file...");
    try {
      const res = await intelligenceApi.generateDossier({
        case_title: `Trajectory Audit: ${query}`,
        summary: `Automated cross-camera route reconstruction across ${routeData.total_cameras} camera sectors with maximum threat evaluation of ${routeData.max_risk_score}%.`,
        route_data: routeData,
      });
      setDossierStatus(`✓ Dossier ${res.case_id} generated. SHA-256 sealed.`);
      window.open(res.download_url, "_blank");
    } catch (e: any) {
      setDossierStatus(`Export error: ${e.message}`);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "10px" }}>
      {/* Header Bar */}
      <div
        style={{
          background: "#0d131a",
          border: "1px solid #1e293b",
          borderRadius: "8px",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "18px", fontWeight: 800, color: "#f8fafc", display: "flex", alignItems: "center", gap: "10px" }}>
              <GitMerge size={20} color="#38bdf8" />
              MULTI-CAMERA SPATIAL-TEMPORAL ROUTE RECONSTRUCTION
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "3px" }}>
              Re-identifies targets across disjoint cameras using multimodal CLIP crop embeddings and topology graphs.
            </div>
          </div>
        </div>

        {/* Query Input */}
        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ flex: 1, position: "relative" }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleReconstruct()}
              placeholder="Describe target to reconstruct cross-camera trajectory (e.g. 'person in red hoodie', 'white sedan')..."
              style={{
                width: "100%",
                background: "#080c12",
                border: "1px solid #334155",
                borderRadius: "6px",
                color: "#f8fafc",
                padding: "10px 14px",
                fontSize: "13px",
                outline: "none",
              }}
            />
          </div>
          <button
            onClick={handleReconstruct}
            disabled={loading}
            style={{
              background: "#0284c7",
              border: "none",
              color: "white",
              padding: "10px 20px",
              borderRadius: "6px",
              fontWeight: 700,
              fontSize: "12px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Sparkles size={16} />
            {loading ? "Reconstructing..." : "Reconstruct Route"}
          </button>
        </div>
      </div>

      {/* Route Trajectory Visualization */}
      {routeData && (
        <div
          style={{
            background: "#0d131a",
            border: "1px solid #1e293b",
            borderRadius: "8px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {/* Metrics Ribbon */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "12px",
              background: "#080c12",
              padding: "12px 16px",
              borderRadius: "6px",
              border: "1px solid #1e293b",
            }}
          >
            <div>
              <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase" }}>Target Entity ID</span>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#38bdf8", fontFamily: "monospace" }}>
                {routeData.entity_id}
              </div>
            </div>
            <div>
              <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase" }}>Cameras Crossed</span>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#f1f5f9" }}>
                {routeData.total_cameras} camera zones
              </div>
            </div>
            <div>
              <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase" }}>Maximum Risk Score</span>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "2px" }}>
                <RiskBadge score={routeData.max_risk_score} severity={routeData.severity_level} size="sm" />
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end" }}>
              <button
                onClick={handleGenerateDossier}
                style={{
                  background: "#be123c",
                  border: "none",
                  color: "white",
                  padding: "8px 14px",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <FileText size={14} />
                Export Forensic Case File
              </button>
            </div>
          </div>

          {dossierStatus && (
            <div style={{ fontSize: "12px", color: "#38bdf8", fontFamily: "monospace" }}>
              {dossierStatus}
            </div>
          )}

          {/* Canvas Component */}
          <RouteMapCanvas
            route={routeData.route}
            onSelectStep={(step) => setSelectedStep(step)}
            selectedStep={selectedStep}
          />
        </div>
      )}
    </div>
  );
};
