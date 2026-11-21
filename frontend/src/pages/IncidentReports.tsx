import React, { useState, useEffect } from "react";
import {
  FileText,
  Download,
  ShieldCheck,
  Hash,
  UserCheck,
  Calendar,
  ExternalLink,
} from "lucide-react";
import { intelligenceApi } from "../services/intelligenceApi";
import type { InvestigationCase } from "../types/intelligence";
import { RiskBadge } from "../components/RiskBadge";

export const IncidentReports: React.FC = () => {
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await intelligenceApi.getCases();
        setCases(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "10px" }}>
      {/* Title */}
      <div>
        <div style={{ fontSize: "18px", fontWeight: 800, color: "#f8fafc", display: "flex", alignItems: "center", gap: "10px" }}>
          <FileText size={20} color="#f43f5e" />
          FORENSIC INCIDENT REPOSITORY &amp; CHAIN OF CUSTODY
        </div>
        <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "3px" }}>
          Certified tamper-evident investigation case files with SHA-256 digital seals for court-admissible evidence presentation.
        </div>
      </div>

      {/* Cases List */}
      <div
        style={{
          background: "#0d131a",
          border: "1px solid #1e293b",
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "14px 20px",
            background: "#080c12",
            borderBottom: "1px solid #1e293b",
            fontSize: "12px",
            fontWeight: 700,
            color: "#94a3b8",
            display: "grid",
            gridTemplateColumns: "140px 1fr 130px 140px 120px",
            alignItems: "center",
          }}
        >
          <span>CASE NUMBER</span>
          <span>INCIDENT SUMMARY</span>
          <span>INVESTIGATOR</span>
          <span>TIMESTAMP</span>
          <span style={{ textAlign: "right" }}>ACTIONS</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          {cases.map((c) => (
            <div
              key={c.id}
              style={{
                padding: "16px 20px",
                borderBottom: "1px solid #182234",
                display: "grid",
                gridTemplateColumns: "140px 1fr 130px 140px 120px",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <div>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "#38bdf8", fontFamily: "monospace" }}>
                  {c.case_number}
                </div>
                <RiskBadge severity={c.threat_level} size="sm" />
              </div>

              <div>
                <div style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc", marginBottom: "4px" }}>
                  {c.title}
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.4" }}>
                  {c.summary}
                </div>
                {c.hash_signature && (
                  <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "monospace", marginTop: "4px" }}>
                    SHA-256: {c.hash_signature}
                  </div>
                )}
              </div>

              <div style={{ fontSize: "11px", color: "#cbd5e1", display: "flex", alignItems: "center", gap: "6px" }}>
                <UserCheck size={14} color="#38bdf8" />
                <span>{c.investigator_id}</span>
              </div>

              <div style={{ fontSize: "11px", color: "#64748b", fontFamily: "monospace" }}>
                {c.created_at}
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <a
                  href={c.pdf_report_path || `/api/intelligence/reports/${c.id}/download`}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    padding: "6px 12px",
                    fontSize: "11px",
                    fontWeight: 700,
                    textDecoration: "none",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Download size={13} />
                  Dossier
                </a>
              </div>
            </div>
          ))}

          {cases.length === 0 && !loading && (
            <div style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
              No certified forensic cases recorded. Generate one from the Route Reconstruction or Investigation page.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
