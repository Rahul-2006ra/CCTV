import { useState } from "react";
import {
  Video,
  Plus,
  MonitorPlay,
  Settings2,
  Trash2,
  Square,
  Maximize2,
  Grid2X2,
  Rows2,
  SquareDashedBottom,
  LayoutGrid,
} from "lucide-react";
import { api, post } from "../services/api";
import type { Camera } from "../types";
import CameraConnection from "../components/CameraConnection";

export default function Cameras({
  cameras,
  refresh,
}: {
  cameras: Camera[];
  refresh: () => void;
}) {
  const [tab, setTab] = useState<"wall" | "setup">("wall");
  const [layout, setLayout] = useState<"1up" | "2up" | "4up" | "auto">("auto");
  const [name, setName] = useState("");
  const [zone, setZone] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function save() {
    setBusy(true);
    setError("");
    try {
      const body = { name, zone: zone.trim() ? JSON.parse(zone) : [] };
      if (editing)
        await api(`/cameras/${editing}`, {
          method: "PATCH",
          body: JSON.stringify(body),
        });
      else await post("/cameras", body);
      setName("");
      setZone("");
      setEditing(null);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function deleteCamera(cid: string) {
    setBusy(true);
    setError("");
    try {
      await api(`/cameras/${cid}`, { method: "DELETE" });
      setDeleting(null);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function quickStop(cid: string) {
    try {
      await post(`/cameras/${cid}/stop`, {});
      refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const activeCamerasCount = cameras.filter(
    (c) => c.live?.status === "RECORDING" || c.live?.status === "CONNECTING"
  ).length;

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">MONITORING & SOURCES / CCTV WALL</p>
          <h1>Cameras & Live Wall</h1>
          <p className="subtitle">
            Continuous multi-camera monitoring wall and camera configuration.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <span className="badge">
            {activeCamerasCount > 0 ? `● ${activeCamerasCount} STREAMING` : "ALL STANDBY"}
          </span>
          <span className="badge">{cameras.length} TOTAL CAMERAS</span>
        </div>
      </div>

      {/* Main View Mode Selector Tabs */}
      <div
        style={{
          display: "flex",
          gap: "10px",
          marginBottom: "20px",
          borderBottom: "1px solid var(--line)",
          paddingBottom: "12px",
        }}
      >
        <button
          className={tab === "wall" ? "primary" : ""}
          onClick={() => setTab("wall")}
        >
          <MonitorPlay size={16} /> Live Monitoring Wall
        </button>
        <button
          className={tab === "setup" ? "primary" : ""}
          onClick={() => setTab("setup")}
        >
          <Settings2 size={16} /> Camera Configuration & Devices
        </button>
      </div>

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {/* VIEW: LIVE MONITORING WALL */}
      {tab === "wall" && (
        <>
          <div className="wall-toolbar">
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <strong>CAMERA MONITORING WALL</strong>
              <small style={{ color: "#8a97a0" }}>
                Continuous low-latency browser streaming
              </small>
            </div>

            <div className="wall-layout-buttons">
              <span style={{ fontSize: "11px", color: "#8a97a0" }}>LAYOUT:</span>
              <button
                className={`icon-button ${layout === "1up" ? "active" : ""}`}
                title="Single Focus (1-Up)"
                onClick={() => setLayout("1up")}
              >
                <SquareDashedBottom size={14} />
              </button>
              <button
                className={`icon-button ${layout === "2up" ? "active" : ""}`}
                title="Split View (2-Up)"
                onClick={() => setLayout("2up")}
              >
                <Rows2 size={14} />
              </button>
              <button
                className={`icon-button ${layout === "4up" ? "active" : ""}`}
                title="Quad Grid (2x2)"
                onClick={() => setLayout("4up")}
              >
                <Grid2X2 size={14} />
              </button>
              <button
                className={`icon-button ${layout === "auto" ? "active" : ""}`}
                title="Responsive Auto Grid"
                onClick={() => setLayout("auto")}
              >
                <LayoutGrid size={14} />
              </button>
            </div>
          </div>

          {!cameras.length ? (
            <div className="empty panel">
              <Video size={36} />
              <h3>No cameras configured yet.</h3>
              <p>Switch to Camera Configuration to add camera locations.</p>
              <button
                className="primary"
                onClick={() => setTab("setup")}
                style={{ marginTop: "12px" }}
              >
                Add Camera Location
              </button>
            </div>
          ) : (
            <div className={`camera-wall-grid layout-${layout}`}>
              {cameras.map((c) => {
                const isLive =
                  c.live?.status === "RECORDING" ||
                  c.live?.status === "CONNECTING";

                return (
                  <div className="wall-tile" key={c.id}>
                    <div className="wall-tile-header">
                      <div>
                        <strong>{c.name}</strong>{" "}
                        <span className="mono" style={{ color: "#7f8f99" }}>
                          ({c.id})
                        </span>
                      </div>
                      <span className="badge">
                        {c.footage_count} footage files
                      </span>
                    </div>

                    <div className="wall-tile-screen">
                      {isLive ? (
                        <>
                          <img
                            src={`/api/cameras/${c.id}/stream`}
                            alt={`Live Stream - ${c.name}`}
                            onError={(e) => {
                              // If stream is reconnecting, fall back to preview frame
                              (e.target as HTMLImageElement).src = `/api/cameras/${c.id}/preview?t=${Date.now()}`;
                            }}
                          />
                          <div className="wall-live-badge">
                            <span className="wall-live-pulse" />
                            LIVE
                          </div>
                          <div className="wall-telemetry">
                            {c.live?.fps || 15} FPS · {c.live?.resolution || "1280x720"}
                          </div>
                          <div className="wall-bottom-bar">
                            <span>
                              {c.live?.segments || 0} segments · {c.live?.elapsed_seconds || 0}s elapsed
                            </span>
                            <button
                              className="icon-button"
                              title="Stop stream & finalize segment"
                              onClick={() => void quickStop(c.id)}
                              style={{
                                padding: "2px 8px",
                                background: "rgba(180, 40, 40, 0.8)",
                                color: "#fff",
                                fontSize: "10px",
                              }}
                            >
                              <Square size={10} /> Stop
                            </button>
                          </div>
                        </>
                      ) : (
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: "8px",
                            color: "#6b7a84",
                          }}
                        >
                          <Video size={40} strokeWidth={1.5} />
                          <div style={{ fontSize: "12px", letterSpacing: "0.5px" }}>
                            CAMERA STANDBY
                          </div>
                          <small style={{ color: "#54646e" }}>
                            {c.live?.message || "Not currently streaming"}
                          </small>
                          <button
                            onClick={() => {
                              setTab("setup");
                            }}
                            style={{
                              marginTop: "8px",
                              fontSize: "11px",
                              padding: "5px 10px",
                            }}
                          >
                            Configure & Connect
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* VIEW: CAMERA CONFIGURATION & SETUP */}
      {tab === "setup" && (
        <>
          <form
            className="panel camera-form"
            onSubmit={(e) => {
              e.preventDefault();
              void save();
            }}
          >
            <h3>
              {editing ? "Edit camera location" : "Add a camera location"}
            </h3>
            <label>
              Location name
              <input
                required
                aria-label="Camera name"
                placeholder="e.g. Main Entrance Gate"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
              />
            </label>
            <label>
              Restricted zone polygon <span className="muted">(optional normalized coordinates)</span>
              <input
                aria-label="Restricted zone polygon"
                placeholder="[[0.1,0.1],[0.8,0.1],[0.8,0.9],[0.1,0.9]]"
                value={zone}
                onChange={(e) => setZone(e.target.value)}
              />
            </label>
            <p className="muted" style={{ fontSize: "11px", marginTop: "4px" }}>
              Coordinates are normalized (0 to 1). Intrusion events trigger alerts when detected persons enter this polygon.
            </p>
            <div className="row-actions">
              <button className="primary" disabled={busy || !name.trim()}>
                <Plus size={15} />
                {editing ? "Save changes" : "Add camera"}
              </button>
              {editing && (
                <button
                  type="button"
                  onClick={() => {
                    setEditing(null);
                    setName("");
                    setZone("");
                  }}
                >
                  Cancel
                </button>
              )}
            </div>
          </form>

          {!cameras.length ? (
            <div className="empty panel">
              <Video size={36} />
              <h3>No cameras configured.</h3>
              <p>Add a location above, then connect streams or upload recordings.</p>
            </div>
          ) : (
            <div className="camera-grid">
              {cameras.map((c) => (
                <article className="panel camera-card" key={c.id}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <Video size={25} color="var(--accent)" />
                    <span className="badge">CAMERA SOURCE</span>
                  </div>

                  <p className="mono" style={{ marginTop: "10px" }}>{c.id}</p>
                  <h3>{c.name}</h3>

                  <dl>
                    <div>
                      <dt>Associated footage</dt>
                      <dd>{c.footage_count} files</dd>
                    </div>
                    <div>
                      <dt>Last activity</dt>
                      <dd>
                        {c.last_activity
                          ? `${new Date(c.last_activity).toLocaleString()}`
                          : "No footage"}
                      </dd>
                    </div>
                    <div>
                      <dt>Restricted zone</dt>
                      <dd>
                        {JSON.parse(c.zone).length
                          ? `${JSON.parse(c.zone).length} vertices`
                          : "Not configured"}
                      </dd>
                    </div>
                  </dl>

                  <div style={{ display: "flex", gap: "8px", margin: "14px 0" }}>
                    <button
                      onClick={() => {
                        setEditing(c.id);
                        setName(c.name);
                        setZone(c.zone === "[]" ? "" : c.zone);
                        window.scrollTo({ top: 0, behavior: "smooth" });
                      }}
                      style={{ fontSize: "11px", flex: 1 }}
                    >
                      Edit zone
                    </button>
                    <button
                      onClick={() => setDeleting(c.id)}
                      style={{
                        fontSize: "11px",
                        color: "#e88574",
                        borderColor: "#57352f",
                      }}
                      title="Delete camera"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>

                  {deleting === c.id && (
                    <div className="delete-confirm" style={{ marginBottom: "14px" }}>
                      <p>
                        Delete camera {c.name}? (Must have 0 associated recordings)
                      </p>
                      <button onClick={() => void deleteCamera(c.id)}>
                        Confirm Delete
                      </button>
                      <button onClick={() => setDeleting(null)}>Cancel</button>
                    </div>
                  )}

                  <CameraConnection camera={c} refresh={refresh} />
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </>
  );
}
