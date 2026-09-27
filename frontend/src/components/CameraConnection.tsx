import { useEffect, useState } from "react";
import { Radio, Square, RefreshCw, Video } from "lucide-react";
import { api, post } from "../services/api";
import type { Camera } from "../types";

export default function CameraConnection({
  camera,
  refresh,
}: {
  camera: Camera;
  refresh: () => void;
}) {
  const [type, setType] = useState("usb");
  const [preset, setPreset] = useState("custom");
  const [url, setUrl] = useState("");
  const [host, setHost] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [channel, setChannel] = useState(1);
  const [minutes, setMinutes] = useState(60);
  const [devices, setDevices] = useState<{ id: string; name: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const live = camera.live;
  const active = ["CONNECTING", "RECORDING", "RECONNECTING", "STOPPING"].includes(
    live?.status || ""
  );

  async function loadDevices() {
    try {
      const items = await api("/camera-devices");
      setDevices(items);
      if (items.length > 0 && !url) {
        setUrl(items[0].id);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    void loadDevices();
  }, []);

  async function connect() {
    setError("");
    setBusy(true);
    try {
      let source = url.trim();
      if (type === "rtsp" && preset !== "custom") {
        if (!host.trim() || /[\s/@?#]/.test(host))
          throw new Error("Enter the camera IP or hostname, optionally followed by :port.");
        const path =
          preset === "hikvision"
            ? `/Streaming/Channels/${channel}01`
            : preset === "dahua"
            ? `/cam/realmonitor?channel=${channel}&subtype=0`
            : "/axis-media/media.amp";
        const auth = username
          ? `${encodeURIComponent(username)}:${encodeURIComponent(password)}@`
          : "";
        source = `rtsp://${auth}${host.trim()}${path}`;
      }
      await post(`/cameras/${camera.id}/connect`, {
        url: source,
        source_type: type,
        duration_minutes: minutes,
      });
      setPassword("");
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="camera-connection">
      <div className="panel-label">
        <strong>LIVE STREAM & CAPTURE</strong>
        <span
          className={`badge ${
            live?.status === "RECORDING"
              ? "ready"
              : live?.status === "FAILED"
              ? "failed"
              : ""
          }`}
        >
          {live?.status || "STOPPED"}
        </span>
      </div>

      {active && (
        <div style={{ position: "relative", marginBottom: "12px" }}>
          <img
            className="live-preview"
            src={`/api/cameras/${camera.id}/stream`}
            alt={`Live stream from ${camera.name}`}
            onError={(e) => {
              // Fallback to preview image if MJPEG stream is initializing
              (e.target as HTMLImageElement).src = `/api/cameras/${camera.id}/preview?t=${Date.now()}`;
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 8,
              left: 8,
              background: "rgba(180, 20, 20, 0.9)",
              color: "#fff",
              padding: "2px 7px",
              borderRadius: "3px",
              fontSize: "10px",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "#fff",
              }}
            />
            LIVE
          </div>

          <div
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              background: "rgba(0, 0, 0, 0.8)",
              color: "#a4b4be",
              fontFamily: "IBM Plex Mono, monospace",
              padding: "2px 6px",
              borderRadius: "3px",
              fontSize: "10px",
            }}
          >
            {live?.fps || 15} FPS · {live?.resolution || "1280x720"}
          </div>

          <div
            style={{
              position: "absolute",
              bottom: 8,
              left: 8,
              right: 8,
              background: "rgba(0, 0, 0, 0.8)",
              color: "#c2d1db",
              padding: "4px 8px",
              borderRadius: "3px",
              fontSize: "10px",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>{live?.segments || 0} segments indexed</span>
            <span>Elapsed: {live?.elapsed_seconds || 0}s</span>
          </div>
        </div>
      )}

      <p role="status" className="muted" style={{ fontSize: "11px", marginBottom: "12px" }}>
        {live?.message || "Select a source to start continuous live stream and automatic indexing."}
      </p>

      {!active && (
        <>
          <label>
            Connection type
            <select
              aria-label={`Connection type for ${camera.name}`}
              value={type}
              onChange={(e) => {
                setType(e.target.value);
                setUrl("");
                setError("");
                if (e.target.value === "usb") void loadDevices();
              }}
            >
              <option value="usb">USB / Built-in camera on this computer</option>
              <option value="rtsp">IP Camera / DVR / NVR (RTSP)</option>
              <option value="http">HTTP stream (HLS / MJPEG)</option>
            </select>
          </label>

          {type === "usb" ? (
            <>
              <label>
                Local Camera Device
                <select
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                >
                  <option value="">Select a camera</option>
                  {devices.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
              <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
                <button type="button" onClick={loadDevices} style={{ fontSize: "11px", padding: "6px 10px" }}>
                  <RefreshCw size={12} /> Scan for cameras
                </button>
              </div>
              <p className="muted" style={{ fontSize: "10px", marginTop: "6px" }}>
                Windows (DirectShow), macOS (AVFoundation), and Linux (v4l2) supported out-of-the-box.
              </p>
            </>
          ) : type === "rtsp" && preset !== "custom" ? (
            <>
              <label>
                Camera IP / hostname
                <input
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder="192.168.1.100:554"
                />
              </label>
              <label>
                Username
                <input
                  autoComplete="off"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              {preset !== "axis" && (
                <label>
                  Recorder channel
                  <input
                    type="number"
                    min={1}
                    max={256}
                    value={channel}
                    onChange={(e) =>
                      setChannel(Math.min(256, Math.max(1, Number(e.target.value))))
                    }
                  />
                </label>
              )}
            </>
          ) : (
            <label>
              Stream URL
              <input
                aria-label={`Stream URL for ${camera.name}`}
                type="password"
                autoComplete="new-password"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={
                  type === "rtsp"
                    ? "rtsp://user:password@camera:554/live"
                    : "https://camera/live/stream.m3u8"
                }
              />
            </label>
          )}

          {type === "rtsp" && (
            <label>
              Camera brand preset
              <select value={preset} onChange={(e) => setPreset(e.target.value)}>
                <option value="custom">Custom stream URL</option>
                <option value="hikvision">Hikvision</option>
                <option value="dahua">Dahua</option>
                <option value="axis">Axis</option>
              </select>
            </label>
          )}

          <label>
            Continuous recording window (minutes)
            <input
              type="number"
              min={1}
              max={480}
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            />
          </label>

          <button
            className="primary"
            disabled={
              busy ||
              minutes < 1 ||
              minutes > 480 ||
              (preset === "custom" || type !== "rtsp" ? !url : !host)
            }
            onClick={connect}
            style={{ width: "100%", marginTop: "10px" }}
          >
            <Radio size={14} />
            {busy ? "Connecting to camera…" : "Connect & Stream Live"}
          </button>
        </>
      )}

      {active && (
        <button
          disabled={busy || live?.status === "STOPPING"}
          onClick={async () => {
            setBusy(true);
            try {
              await post(`/cameras/${camera.id}/stop`, {});
              refresh();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
          style={{ width: "100%", marginTop: "10px", borderColor: "#7a3e36", color: "#f2a89b" }}
        >
          <Square size={14} /> Stop recording
        </button>
      )}

      {error && (
        <p className="error" role="alert" style={{ marginTop: "10px", fontSize: "11px" }}>
          {error}
        </p>
      )}
    </div>
  );
}
