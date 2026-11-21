import { useCallback, useEffect, useState } from "react";
import {
  Shield,
  LayoutDashboard,
  ScanLine,
  Film,
  Video,
  Bell,
  HardDrive,
  GitMerge,
  BarChart3,
  FileText,
  Radio,
  Bot,
  Activity,
} from "lucide-react";
import { api } from "./services/api";
import { intelligenceApi } from "./services/intelligenceApi";
import type { Camera, Video as VideoType } from "./types";
import type { ThreatStatus } from "./types/intelligence";
import Investigation from "./pages/Investigation";
import Footage from "./pages/Footage";
import Cameras from "./pages/Cameras";
import Alerts from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import { CommandCenter } from "./pages/CommandCenter";
import { RouteReconstruction } from "./pages/RouteReconstruction";
import { ThreatAnalytics } from "./pages/ThreatAnalytics";
import { IncidentReports } from "./pages/IncidentReports";
import { CopilotChatDrawer } from "./components/CopilotChatDrawer";
import { RiskBadge } from "./components/RiskBadge";
import { ErrorBoundary } from "./components/ErrorBoundary";

const routes: Record<string, string> = {
  "Command Center": "/command-center",
  "Route Reconstruction": "/routes",
  Investigation: "/investigation",
  "Threat Analytics": "/analytics",
  "Forensic Cases": "/cases",
  Dashboard: "/dashboard",
  Footage: "/footage",
  Cameras: "/cameras",
  Alerts: "/alerts",
};

const currentPage = () =>
  Object.keys(routes).find((k) => routes[k] === window.location.pathname) ||
  "Command Center";

const nav = [
  ["Command Center", Radio],
  ["Route Reconstruction", GitMerge],
  ["Investigation", ScanLine],
  ["Threat Analytics", BarChart3],
  ["Forensic Cases", FileText],
  ["Dashboard", LayoutDashboard],
  ["Footage", Film],
  ["Cameras", Video],
  ["Alerts", Bell],
] as const;

export default function App() {
  const [page, setPageState] = useState(currentPage);
  const [health, setHealth] = useState<any>(null);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [threatStatus, setThreatStatus] = useState<ThreatStatus | null>(null);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [error, setError] = useState("");
  const [initial, setInitial] = useState<any>(null);
  const [searchKey, setSearchKey] = useState(0);

  function setPage(value: string) {
    setPageState(value);
    if (window.location.pathname !== routes[value])
      window.history.pushState({}, "", routes[value]);
  }

  useEffect(() => {
    const update = () => setPageState(currentPage());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [h, c, v, a, d] = await Promise.all([
        api("/system/health"),
        api("/cameras"),
        api("/videos"),
        api("/alerts"),
        api("/dashboard"),
      ]);
      setHealth(h);
      setCameras(c);
      setVideos(v);
      setAlerts(a);
      setDashboard(d);
      setError("");

      try {
        const threat = await intelligenceApi.getThreatStatus();
        setThreatStatus(threat);
      } catch {
        // Fallback
      }
    } catch (e) {
      setHealth(null);
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, [refresh]);

  async function openSearch(id: string) {
    try {
      setInitial(await api(`/search/${id}`));
      setSearchKey((k) => k + 1);
      setPage("Investigation");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand" style={{ cursor: "pointer" }} onClick={() => setPage("Command Center")}>
          <div className="brand-mark" style={{ background: "#0284c7", color: "white" }}>
            <Shield size={24} />
          </div>
          <div>
            SENTINEL<span style={{ color: "#38bdf8" }}>AI</span>
          </div>
        </div>

        <div style={{ padding: "0 14px 10px 14px" }}>
          <div
            style={{
              background: "#080c12",
              border: "1px solid #1e293b",
              borderRadius: "4px",
              padding: "6px 10px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>SYSTEM STATUS</span>
            <RiskBadge
              score={threatStatus?.global_risk_score || 25}
              severity={threatStatus?.threat_level || "GUARDED"}
              size="sm"
            />
          </div>
        </div>

        <p className="nav-label">INTELLIGENCE PLATFORM</p>
        <nav>
          {nav.map(([label, Icon]) => (
            <button
              aria-label={label}
              title={label}
              className={page === label ? "active" : ""}
              key={label}
              onClick={() => setPage(label)}
            >
              <Icon size={17} />
              <span>{label}</span>
              {label === "Alerts" && alerts.some((a) => a.status === "NEW") && (
                <b>{alerts.filter((a) => a.status === "NEW").length}</b>
              )}
            </button>
          ))}
        </nav>

        <div style={{ padding: "14px" }}>
          <button
            onClick={() => setCopilotOpen(true)}
            style={{
              width: "100%",
              background: "#0369a1",
              border: "1px solid #38bdf8",
              color: "white",
              padding: "8px",
              borderRadius: "4px",
              fontWeight: 700,
              fontSize: "11px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              cursor: "pointer",
              boxShadow: "0 0 10px rgba(56, 189, 248, 0.3)",
            }}
          >
            <Bot size={15} />
            <span>AI COPILOT AGENT</span>
          </button>
        </div>

        <div className="sidebar-bottom">
          <HardDrive size={17} />
          <div>
            Edge Intelligence<small>On-device neural inference</small>
          </div>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            SENTINELAI <span className="slash">/</span> <strong>{page}</strong>
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span className={`dot ${health ? "" : "offline"}`} />
            {health ? "Telemetry Active" : "Connecting"}
            <span className="divider" />
            {health?.device || "Neural Core"}
            <span className="badge">
              {health?.acceleration?.toUpperCase() || "CPU/MPS"}
            </span>
          </div>
        </header>

        <main>
          <ErrorBoundary>
            {error && (
              <div role="alert" className="error">
                Backend connection: {error}. Check that the backend is running on
                port 8000.
              </div>
            )}

            {page === "Command Center" && (
              <CommandCenter cameras={cameras} videos={videos} alerts={alerts} />
            )}

            {page === "Route Reconstruction" && <RouteReconstruction />}

            {page === "Threat Analytics" && <ThreatAnalytics />}

            {page === "Forensic Cases" && <IncidentReports />}

            {page === "Dashboard" && (
              <Dashboard
                data={dashboard}
                health={health}
                navigate={setPage}
                openSearch={openSearch}
              />
            )}

            <div hidden={page !== "Investigation"}>
              <Investigation
                key={searchKey}
                cameras={cameras}
                videos={videos}
                initial={initial}
                onInitialConsumed={() => setInitial(null)}
              />
            </div>

            {page === "Footage" && (
              <Footage
                cameras={cameras}
                videos={videos}
                refresh={refresh}
                onInvestigate={(q, cid, vid, fname) => {
                  setInitial({
                    query: q || "",
                    camera_id: cid,
                    video_id: vid,
                    video_filename: fname,
                    clues: q ? [q] : [],
                  });
                  setSearchKey((k) => k + 1);
                  setPage("Investigation");
                }}
              />
            )}

            {page === "Cameras" && (
              <Cameras cameras={cameras} refresh={refresh} />
            )}

            {page === "Alerts" && <Alerts alerts={alerts} refresh={refresh} />}
          </ErrorBoundary>
        </main>

        <footer className="app-footer">
          <span>
            SENTINELAI <span className="muted">/ AUTONOMOUS SURVEILLANCE INTELLIGENCE</span>
          </span>
          <span>Zero-Shot Threat Detection &bull; Multi-Camera Trajectory Re-ID &bull; Forensic Provenance</span>
        </footer>
      </div>

      <CopilotChatDrawer isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </div>
  );
}
