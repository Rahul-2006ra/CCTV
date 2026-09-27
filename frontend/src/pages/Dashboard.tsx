import {
  Video,
  Film,
  Activity,
  Clock,
  ArrowUpRight,
  Database,
  Radio,
  Cpu,
  Layers,
  Search,
  Upload,
  MonitorPlay,
  CheckCircle2,
} from "lucide-react";
import { time } from "../services/api";

export default function Dashboard({
  data,
  health,
  navigate,
  openSearch,
}: {
  data: any;
  health: any;
  navigate: (s: string) => void;
  openSearch: (id: string) => void;
}) {
  function formatFreeDisk(bytes?: number) {
    if (!bytes) return "—";
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(1)} GB free`;
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">OVERVIEW / LOCAL WORKSPACE</p>
          <h1>Operations Overview</h1>
          <p className="subtitle">
            CCTV surveillance intelligence, real-time live capture, and vector search operations.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={() => navigate("Footage")}>
            <Upload size={14} /> Upload footage
          </button>
          <button className="primary" onClick={() => navigate("Investigation")}>
            New investigation
            <ArrowUpRight size={16} />
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="stats-grid">
        <div className="panel stat">
          <Radio size={20} color="var(--accent)" />
          <span>Live Cameras</span>
          <strong>
            {data?.live_cameras ?? 0} <small style={{ fontSize: "13px", fontWeight: "normal", color: "#8a98a0" }}>/ {data?.cameras ?? 0} configured</small>
          </strong>
        </div>

        <div className="panel stat">
          <Film size={20} />
          <span>Indexed Recordings</span>
          <strong>{data?.indexed ?? 0}</strong>
        </div>

        <div className="panel stat">
          <Clock size={20} />
          <span>Footage Duration</span>
          <strong>{data ? time(data.duration) : "00:00"}</strong>
        </div>

        <div className="panel stat">
          <Database size={20} color="#9ec5db" />
          <span>Visual Embeddings</span>
          <strong>{(data?.vectors ?? health?.vectors ?? 0).toLocaleString()}</strong>
        </div>
      </div>

      {/* System Engine Status Strip */}
      <div
        className="panel"
        style={{
          padding: "16px 20px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "14px",
          background: "#161b1e",
          border: "1px solid #283035",
          borderRadius: "6px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span className={`dot ${health ? "" : "offline"}`} />
          <strong>AI Pipeline Engine:</strong>
          <span style={{ color: "#a5b4bc", fontSize: "12px" }}>
            {health ? "Fully Operational" : "Initializing…"}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap", fontSize: "11px" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <Cpu size={13} color="var(--accent)" /> YOLOv8n ({health?.detector_acceleration || "CPU"})
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <Layers size={13} color="var(--accent)" /> CLIP ViT-B/32 ({health?.acceleration || "CPU"})
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <Database size={13} color="#9ec5db" /> Qdrant ({health?.vector_db || "Connected"})
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#8a98a0" }}>
            Storage: {formatFreeDisk(health?.storage_free_bytes)}
          </span>
        </div>

        <button
          onClick={() => navigate("Cameras")}
          style={{ fontSize: "11px", padding: "6px 12px" }}
        >
          <MonitorPlay size={13} /> Open Camera Wall
        </button>
      </div>

      {/* Recent Investigations & Alerts */}
      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-label">
            RECENT INVESTIGATIONS
            <SearchLink onClick={() => navigate("Investigation")} />
          </div>
          {data?.searches.length ? (
            data.searches.map((s: any) => (
              <button
                className="list-row"
                key={s.id}
                onClick={() => openSearch(s.id)}
              >
                <span>
                  <strong>{s.query}</strong>
                  <small>{new Date(s.created_at).toLocaleString()}</small>
                </span>
                <ArrowUpRight size={16} />
              </button>
            ))
          ) : (
            <div className="empty compact">
              No investigations yet. Try searching for "person in red shirt" or "white car".
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-label">
            RECENT ALERTS
            <SearchLink onClick={() => navigate("Alerts")} />
          </div>
          {data?.alerts.length ? (
            data.alerts.map((a: any) => (
              <button
                className="list-row"
                key={a.id}
                onClick={() => navigate("Alerts")}
              >
                <span>
                  <strong>{a.event_type}</strong>
                  <small>
                    Camera: {a.camera_id} · {time(a.timestamp)}
                  </small>
                </span>
                <span className={`badge ${a.status === "NEW" ? "failed" : "ready"}`}>
                  {a.status}
                </span>
              </button>
            ))
          ) : (
            <div className="empty compact">No active rule alerts.</div>
          )}
        </section>
      </div>

      {/* System Health Footer Strip */}
      <section className="panel health-strip" style={{ marginTop: "24px" }}>
        <div>
          <span className={`dot ${health ? "" : "offline"}`} />
          <strong>
            {health ? "CCTV Intelligence Server Online" : "Backend Disconnected"}
          </strong>
        </div>
        <span>Device: {health?.device || "Local host"}</span>
        <span>FFmpeg: {health?.ffmpeg || "Available"}</span>
        <span>Sample Rate: {health?.sample_fps || 1} FPS</span>
      </section>
    </>
  );
}

function SearchLink({ onClick }: { onClick: () => void }) {
  return (
    <button className="text-button" onClick={onClick}>
      View all
      <ArrowUpRight size={13} />
    </button>
  );
}
