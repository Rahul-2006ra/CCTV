import React, { useState } from "react";
import { Bot, Send, X, ShieldAlert, Sparkles, ChevronRight } from "lucide-react";
import { intelligenceApi } from "../services/intelligenceApi";
import type { CopilotResponse } from "../types/intelligence";
import { RiskBadge } from "./RiskBadge";

interface CopilotChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CopilotChatDrawer: React.FC<CopilotChatDrawerProps> = ({ isOpen, onClose }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ sender: "user" | "copilot"; text: string; data?: CopilotResponse }>>([
    {
      sender: "copilot",
      text: "SENTINELAI COPILOT ACTIVE // Ready to analyze multi-camera feeds, correlate target trajectories, or draft tactical briefings. What is your directive?",
    },
  ]);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  async function handleSend(textToSend?: string) {
    const q = (textToSend || input).trim();
    if (!q || loading) return;

    const userMsg = { sender: "user" as const, text: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await intelligenceApi.queryCopilot(q);
      setMessages((prev) => [
        ...prev,
        {
          sender: "copilot",
          text: res.response,
          data: res,
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "copilot",
          text: `[SYSTEM ALERT] Copilot inquiry failed: ${e.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const quickPrompts = [
    "Summarize all high-risk perimeter breaches",
    "Identify any abandoned backpacks or payloads",
    "Reconstruct route of suspect with face concealed",
  ];

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: "440px",
        height: "100vh",
        background: "#0b0f17",
        borderLeft: "1px solid #1e293b",
        boxShadow: "-10px 0 30px rgba(0, 0, 0, 0.7)",
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid #1e293b",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "#0f172a",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "4px",
              background: "#0284c7",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
            }}
          >
            <Bot size={18} />
          </div>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc", letterSpacing: "0.04em" }}>
              SENTINELAI COPILOT
            </div>
            <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>
              TACTICAL INVESTIGATION REASONER
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", padding: "4px" }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Quick Prompt Bar */}
      <div style={{ padding: "10px 16px", background: "#090d16", borderBottom: "1px solid #1e293b" }}>
        <div style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase", marginBottom: "6px", fontWeight: 700 }}>
          Suggested Inquiries
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
          {quickPrompts.map((p, i) => (
            <div
              key={i}
              onClick={() => handleSend(p)}
              style={{
                fontSize: "11px",
                color: "#94a3b8",
                background: "#131b29",
                border: "1px solid #1e293b",
                padding: "5px 8px",
                borderRadius: "4px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span>{p}</span>
              <ChevronRight size={12} color="#38bdf8" />
            </div>
          ))}
        </div>
      </div>

      {/* Message History */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: "14px" }}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.sender === "user" ? "flex-end" : "flex-start",
              maxWidth: "88%",
              background: m.sender === "user" ? "#0369a1" : "#131b29",
              color: "#f1f5f9",
              padding: "12px 14px",
              borderRadius: "6px",
              fontSize: "12px",
              lineHeight: 1.5,
              border: m.sender === "user" ? "1px solid #38bdf8" : "1px solid #1e293b",
              fontFamily: m.sender === "copilot" ? "'JetBrains Mono', monospace, sans-serif" : "inherit",
              whiteSpace: "pre-wrap",
            }}
          >
            {m.data && (
              <div style={{ marginBottom: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
                <RiskBadge severity={m.data.threat_level} size="sm" />
                <span style={{ fontSize: "10px", color: "#94a3b8" }}>
                  {m.data.matched_events_count} events correlated
                </span>
              </div>
            )}
            {m.text}
          </div>
        ))}
        {loading && (
          <div style={{ color: "#38bdf8", fontSize: "11px", fontFamily: "monospace", display: "flex", alignItems: "center", gap: "6px" }}>
            <Sparkles size={14} className="spin" />
            Synthesizing spatial-temporal intelligence graph...
          </div>
        )}
      </div>

      {/* Input Form */}
      <div style={{ padding: "14px", borderTop: "1px solid #1e293b", background: "#0f172a", display: "flex", gap: "8px" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Issue directive or ask threat question..."
          style={{
            flex: 1,
            background: "#090d16",
            border: "1px solid #334155",
            borderRadius: "4px",
            color: "#f8fafc",
            padding: "8px 12px",
            fontSize: "12px",
            outline: "none",
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            background: "#0284c7",
            border: "none",
            color: "white",
            padding: "8px 14px",
            borderRadius: "4px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
};
