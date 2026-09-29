import { useRef, useState, useMemo } from "react";
import {
  Upload,
  RefreshCw,
  Trash2,
  Film,
  Play,
  Search,
  SlidersHorizontal,
  Eye,
  X,
  ArrowUpRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  Video as VideoIcon,
  Layers,
  LayoutGrid,
} from "lucide-react";
import { api, post, time } from "../services/api";
import type { Camera, Video } from "../types";

export default function Footage({
  cameras,
  videos,
  refresh,
  onInvestigate,
}: {
  cameras: Camera[];
  videos: Video[];
  refresh: () => void;
  onInvestigate?: (query?: string, camId?: string, videoId?: string, videoFilename?: string) => void;
}) {
  const [camera, setCamera] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState<{ [id: string]: "deleting" | "indexing" }>({});
  const [cardErrors, setCardErrors] = useState<{ [id: string]: string }>({});
  const [uploadProgress, setUploadProgress] = useState<{
    fileName: string;
    percent: number;
    loadedMB: string;
    totalMB: string;
    speedMBs: string;
  } | null>(null);

  // Toolbar state
  const [searchQuery, setSearchQuery] = useState("");
  const [cameraFilter, setCameraFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("newest");
  const [viewMode, setViewMode] = useState<"grouped" | "grid">("grouped");

  // Video Inspection Modal state
  const [activeModalVideo, setActiveModalVideo] = useState<Video | null>(null);

  const input = useRef<HTMLInputElement>(null);

  async function upload(file?: File) {
    if (!file) return;
    setBusy(true);
    setError("");
    setUploadProgress({
      fileName: file.name,
      percent: 0,
      loadedMB: "0.0",
      totalMB: (file.size / (1024 * 1024)).toFixed(1),
      speedMBs: "0.0",
    });

    try {
      let cid = camera || cameras[0]?.id;
      if (!cid || cid === "auto") {
        if (cameras.length > 0) {
          cid = cameras[0].id;
        } else {
          try {
            const newCam = await post<Camera>("/cameras", {
              name: "Main Camera (Default)",
              zone: [],
            });
            cid = newCam.id;
          } catch {
            cid = "CAM-MAIN";
          }
        }
      }
      const data = new FormData();
      data.append("file", file);
      if (cid && cid !== "auto") {
        data.append("camera_id", cid);
      }

      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const startTime = Date.now();

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.min(99, Math.round((event.loaded / event.total) * 100));
            const now = Date.now();
            const elapsed = Math.max(0.1, (now - startTime) / 1000);
            const speed = (event.loaded / (1024 * 1024 * elapsed)).toFixed(1);
            setUploadProgress({
              fileName: file.name,
              percent,
              loadedMB: (event.loaded / (1024 * 1024)).toFixed(1),
              totalMB: (event.total / (1024 * 1024)).toFixed(1),
              speedMBs: speed,
            });
          }
        };

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            setUploadProgress({
              fileName: file.name,
              percent: 100,
              loadedMB: (file.size / (1024 * 1024)).toFixed(1),
              totalMB: (file.size / (1024 * 1024)).toFixed(1),
              speedMBs: "Complete",
            });
            resolve();
          } else {
            let errorMsg = `Upload failed (HTTP ${xhr.status})`;
            try {
              const res = JSON.parse(xhr.responseText);
              errorMsg = res.detail || errorMsg;
            } catch {}
            reject(new Error(errorMsg));
          }
        };

        xhr.onerror = () => reject(new Error("Network error during video upload"));
        xhr.ontimeout = () => reject(new Error("Video upload timed out"));

        xhr.open("POST", "/api/videos");
        xhr.send(data);
      });

      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      setUploadProgress(null);
      if (input.current) input.current.value = "";
    }
  }

  async function action(id: string, remove = false) {
    try {
      setError("");
      setCardErrors((prev) => ({ ...prev, [id]: "" }));
      setActionBusy((prev) => ({ ...prev, [id]: remove ? "deleting" : "indexing" }));

      if (remove) {
        await api(`/videos/${id}`, { method: "DELETE" });
        if (activeModalVideo?.id === id) setActiveModalVideo(null);
        setDeleting(null);
      } else {
        await post(`/videos/${id}/process`, {});
      }
      refresh();
    } catch (e) {
      const msg = (e as Error).message;
      setError(msg);
      setCardErrors((prev) => ({ ...prev, [id]: msg }));
    } finally {
      setActionBusy((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    }
  }

  // Filter & sort videos
  const filteredVideos = useMemo(() => {
    return videos
      .filter((v) => {
        // Text search
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const cam = cameras.find((c) => c.id === v.camera_id);
          const matchFilename = v.filename.toLowerCase().includes(q);
          const matchCam = cam?.name.toLowerCase().includes(q) || v.camera_id.toLowerCase().includes(q);
          const matchCodec = v.codec?.toLowerCase().includes(q);
          if (!matchFilename && !matchCam && !matchCodec) return false;
        }
        // Camera filter
        if (cameraFilter !== "all" && v.camera_id !== cameraFilter) return false;
        // Status filter
        if (statusFilter === "READY" && v.status !== "READY") return false;
        if (statusFilter === "FAILED" && v.status !== "FAILED") return false;
        if (statusFilter === "PROCESSING" && (v.status === "READY" || v.status === "FAILED")) return false;
        return true;
      })
      .sort((a, b) => {
        if (sortBy === "newest") {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        }
        if (sortBy === "oldest") {
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        }
        if (sortBy === "duration") {
          return b.duration - a.duration;
        }
        if (sortBy === "size") {
          return b.size - a.size;
        }
        return 0;
      });
  }, [videos, cameras, searchQuery, cameraFilter, statusFilter, sortBy]);

  // Grouped by camera
  const groupedVideos = useMemo(() => {
    const map = new Map<string, Video[]>();
    for (const v of filteredVideos) {
      const list = map.get(v.camera_id) || [];
      list.push(v);
      map.set(v.camera_id, list);
    }
    // Also include cameras matching filter even if empty if no search query
    if (!searchQuery.trim() && statusFilter === "all") {
      for (const cam of cameras) {
        if (cameraFilter === "all" || cameraFilter === cam.id) {
          if (!map.has(cam.id)) {
            map.set(cam.id, []);
          }
        }
      }
    }
    return map;
  }, [filteredVideos, cameras, cameraFilter, searchQuery, statusFilter]);

  function formatBytes(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }

  function renderVideoCard(v: Video) {
    const cam = cameras.find((c) => c.id === v.camera_id);
    const thumbUrl = `/media/thumbnails/${v.id}_0.jpg`;
    const isProcessing = v.status !== "READY" && v.status !== "FAILED";

    return (
      <article className="footage-card" key={v.id}>
        <div
          className="footage-card-thumb"
          onClick={() => setActiveModalVideo(v)}
          title={`Click to view ${v.filename}`}
        >
          <img
            src={thumbUrl}
            alt={v.filename}
            onError={(e) => {
              (e.target as HTMLElement).style.display = "none";
            }}
          />
          <div className="thumb-overlay">
            <Play size={36} color="#fff" />
          </div>
          <span className={`badge-status ${v.status.toLowerCase()}`}>
            {v.status === "READY"
              ? "● READY"
              : v.status === "FAILED"
              ? "● FAILED"
              : `● ${v.status} ${Math.round(v.progress)}%`}
          </span>
          <span className="badge-duration">{time(v.duration)}</span>
        </div>

        <div className="footage-card-body">
          <div className="footage-card-title" title={v.filename}>
            {v.filename}
          </div>

          <div className="footage-card-specs">
            <span>{cam?.name || v.camera_id}</span>
            <span>·</span>
            <span>{formatBytes(v.size)}</span>
            <span>·</span>
            <span>{new Date(v.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          </div>

          <div className="footage-card-specs">
            <span>
              {v.width}×{v.height} · {v.fps.toFixed(0)} FPS · {v.codec}
            </span>
          </div>

          {isProcessing && (
            <div style={{ marginTop: "4px" }}>
              <progress value={v.progress} max="100" />
            </div>
          )}

          {v.error && <small className="error-text">{v.error}</small>}

          <div className="footage-card-metrics">
            <span className="metric-chip" title="Total sampled video frames">
              {v.frames} frames
            </span>
            <span className="metric-chip" title="YOLOv8 detected objects">
              {v.objects} detections
            </span>
            <span className="metric-chip" title="CLIP visual embeddings in Qdrant">
              {v.embeddings} vectors
            </span>
          </div>
        </div>

        <div className="footage-card-actions">
          <div style={{ display: "flex", gap: "6px" }}>
            <button
              className="icon-button"
              title="Inspect & Play Video"
              onClick={() => setActiveModalVideo(v)}
            >
              <Eye size={14} />
            </button>
            <button
              className="icon-button"
              title="Search in Investigation (Scope to this video)"
              onClick={() => {
                if (onInvestigate) {
                  onInvestigate("", v.camera_id, v.id, v.filename);
                }
              }}
            >
              <Search size={14} />
            </button>
            <button
              style={{
                fontSize: "11px",
                padding: "3px 8px",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                background: "rgba(100, 255, 120, 0.12)",
                color: "var(--accent)",
                border: "1px solid rgba(100, 255, 120, 0.3)",
                borderRadius: "4px",
                cursor: "pointer",
              }}
              title="Investigate this specific video"
              onClick={() => {
                if (onInvestigate) {
                  onInvestigate("", v.camera_id, v.id, v.filename);
                }
              }}
            >
              <Search size={11} /> Investigate
            </button>
            <button
              className="icon-button"
              title={actionBusy[v.id] === "indexing" ? "Re-indexing..." : "Re-index footage"}
              disabled={actionBusy[v.id] === "indexing"}
              onClick={() => void action(v.id)}
            >
              <RefreshCw
                size={14}
                className={actionBusy[v.id] === "indexing" || v.status === "PROCESSING" ? "spin" : ""}
              />
            </button>
          </div>

          <div>
            <button
              className="icon-button"
              title="Delete video"
              style={{ color: "#e07a68" }}
              disabled={actionBusy[v.id] === "deleting"}
              onClick={() => setDeleting(v.id)}
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        {deleting === v.id && (
          <div className="delete-confirm" style={{ margin: "10px 16px" }}>
            <p>
              {v.status === "PROCESSING"
                ? "Cancel active processing and delete this video, clips, and vectors?"
                : "Delete this video, clips, and vectors?"}
            </p>
            <button
              style={{
                background: "#e07a68",
                color: "#fff",
                border: "none",
                borderRadius: "3px",
                padding: "5px 12px",
                cursor: "pointer",
                fontWeight: 600,
              }}
              disabled={actionBusy[v.id] === "deleting"}
              onClick={() => void action(v.id, true)}
            >
              {actionBusy[v.id] === "deleting" ? "Deleting…" : "Delete"}
            </button>
            <button
              disabled={actionBusy[v.id] === "deleting"}
              onClick={() => setDeleting(null)}
              style={{ padding: "5px 12px", cursor: "pointer" }}
            >
              Cancel
            </button>
          </div>
        )}
        {cardErrors[v.id] && (
          <div
            className="error"
            style={{ margin: "8px 16px 12px", fontSize: "11px", padding: "6px 10px" }}
          >
            {cardErrors[v.id]}
          </div>
        )}
      </article>
    );
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">LIBRARY / VIDEO SOURCES</p>
          <h1>Footage Library</h1>
          <p className="subtitle">
            Upload, index, and organize your CCTV footage recordings by camera.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <span className="badge">{videos.length} RECORDINGS</span>
          <span className="badge">{cameras.length} CAMERAS</span>
        </div>
      </div>

      {/* Upload panel */}
      <div
        className="panel upload-panel"
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          const file = e.dataTransfer.files?.[0];
          if (file) void upload(file);
        }}
      >
        <Upload size={28} />
        <div>
          <h3>Add footage to the investigation index</h3>
          <p>
            MP4, MKV, WebM, MOV, AVI · Local processing ·{" "}
            {busy
              ? "Uploading and queueing for YOLOv8 & CLIP…"
              : "Videos are automatically indexed with YOLOv8, ByteTrack, and CLIP. (Drag & drop files here)"}
          </p>
        </div>
        <select
          aria-label="Upload camera"
          value={camera || cameras[0]?.id || "auto"}
          onChange={(e) => setCamera(e.target.value)}
        >
          {!cameras.length && (
            <option value="auto">Main Camera (Auto-create)</option>
          )}
          {cameras.map((c) => (
            <option value={c.id} key={c.id}>
              {c.name} ({c.id})
            </option>
          ))}
        </select>
        <button
          className="primary"
          disabled={busy}
          onClick={() => input.current?.click()}
        >
          <Upload size={15} />
          {busy ? "Uploading…" : "Upload footage"}
        </button>
        <input
          ref={input}
          data-testid="video-upload"
          type="file"
          accept="video/*,.mp4,.mov,.avi,.mkv,.webm,.m4v,.wmv,.flv,.ts"
          hidden
          onChange={(e) => void upload(e.target.files?.[0])}
        />
      </div>

      {uploadProgress && (
        <div
          style={{
            marginBottom: "16px",
            padding: "16px 20px",
            background: "#182226",
            border: "1px solid var(--accent)",
            borderRadius: "8px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "10px",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Upload size={18} color="var(--accent)" />
              <span style={{ fontWeight: 600, color: "#fff", fontSize: "14px" }}>
                Streaming Large Video:{" "}
                <span className="mono" style={{ color: "#d0d7de" }}>{uploadProgress.fileName}</span>
              </span>
              <span
                style={{
                  background: "rgba(82, 196, 26, 0.2)",
                  color: "var(--accent)",
                  padding: "2px 8px",
                  borderRadius: "12px",
                  fontSize: "12px",
                  fontWeight: 700,
                }}
              >
                {uploadProgress.percent}%
              </span>
            </div>
            <span className="mono" style={{ fontSize: "12px", color: "#8c98a0" }}>
              {uploadProgress.loadedMB} / {uploadProgress.totalMB} MB ({uploadProgress.speedMBs} MB/s)
            </span>
          </div>
          <div
            style={{
              width: "100%",
              height: "10px",
              background: "#243238",
              borderRadius: "5px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${uploadProgress.percent}%`,
                height: "100%",
                background: "linear-gradient(90deg, #389e0d, var(--accent))",
                transition: "width 0.2s ease",
              }}
            />
          </div>
          <div style={{ marginTop: "8px", fontSize: "12px", color: "#8c98a0", display: "flex", justifyContent: "space-between" }}>
            <span>Reading and streaming large video file directly to disk storage...</span>
            <span>YOLOv8 & CLIP indexing will start automatically</span>
          </div>
        </div>
      )}

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {/* Toolbar: Search, Filters, Sorters, View Mode */}
      <div className="footage-toolbar">
        <div className="footage-search-wrap">
          <Search size={16} color="#7f8e99" />
          <input
            placeholder="Search by filename, camera name, codec…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              className="icon-button"
              style={{ background: "transparent", border: "none", padding: "0" }}
              onClick={() => setSearchQuery("")}
            >
              <X size={14} />
            </button>
          )}
        </div>

        <div className="footage-filters">
          <select
            value={cameraFilter}
            onChange={(e) => setCameraFilter(e.target.value)}
            aria-label="Filter by camera"
          >
            <option value="all">All Cameras ({videos.length})</option>
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({videos.filter((v) => v.camera_id === c.id).length})
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by status"
          >
            <option value="all">All Statuses</option>
            <option value="READY">Ready</option>
            <option value="PROCESSING">Processing</option>
            <option value="FAILED">Failed</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            aria-label="Sort recordings"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="duration">Longest Duration</option>
            <option value="size">Largest Size</option>
          </select>

          <div style={{ display: "flex", gap: "4px" }}>
            <button
              className={`icon-button ${viewMode === "grouped" ? "active" : ""}`}
              style={{
                background: viewMode === "grouped" ? "#2c383f" : "#1b2124",
                borderColor: viewMode === "grouped" ? "var(--accent)" : "#343d42",
              }}
              title="Group by Camera"
              onClick={() => setViewMode("grouped")}
            >
              <Layers size={14} />
            </button>
            <button
              className={`icon-button ${viewMode === "grid" ? "active" : ""}`}
              style={{
                background: viewMode === "grid" ? "#2c383f" : "#1b2124",
                borderColor: viewMode === "grid" ? "var(--accent)" : "#343d42",
              }}
              title="Flat Grid"
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {!filteredVideos.length ? (
        <div className="empty panel">
          <Film size={36} />
          <h3>No recordings match your criteria.</h3>
          <p>
            {videos.length === 0
              ? "Select a video file to begin automated AI indexing."
              : "Try adjusting your search query or filters."}
          </p>
          {videos.length === 0 && (
            <button
              className="primary"
              style={{ marginTop: "16px" }}
              disabled={busy}
              onClick={() => input.current?.click()}
            >
              <Upload size={16} /> Select video to upload
            </button>
          )}
        </div>
      ) : viewMode === "grid" ? (
        <div className="footage-grid" style={{ borderRadius: "6px", borderTop: "1px solid var(--line)" }}>
          {filteredVideos.map(renderVideoCard)}
        </div>
      ) : (
        Array.from(groupedVideos.entries()).map(([cid, vids]) => {
          const cam = cameras.find((c) => c.id === cid);
          return (
            <section className="footage-camera-group" key={cid}>
              <div className="footage-group-header">
                <div className="cam-info">
                  <VideoIcon size={20} color="var(--accent)" />
                  <div>
                    <h3>{cam?.name || cid}</h3>
                    <small style={{ color: "#8c98a0" }}>
                      ID: <span className="mono">{cid}</span> · {vids.length} recordings
                      {cam?.live?.status === "RECORDING" && " · ● LIVE RECORDING"}
                    </small>
                  </div>
                </div>

                <div>
                  <button
                    onClick={() => {
                      setCamera(cid);
                      input.current?.click();
                    }}
                    style={{ fontSize: "11px", padding: "6px 10px" }}
                  >
                    <Upload size={12} /> Upload to this camera
                  </button>
                </div>
              </div>

              {vids.length === 0 ? (
                <div
                  className="empty compact"
                  style={{
                    padding: "24px",
                    background: "#14181b",
                    border: "1px solid var(--line)",
                    borderTop: "none",
                    borderRadius: "0 0 6px 6px",
                  }}
                >
                  No recordings uploaded for this camera yet.
                </div>
              ) : (
                <div className="footage-grid">{vids.map(renderVideoCard)}</div>
              )}
            </section>
          );
        })
      )}

      {/* Video Modal Inspector */}
      {activeModalVideo && (
        <div className="modal-backdrop" onClick={() => setActiveModalVideo(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <Film size={18} color="var(--accent)" />
                <span>{activeModalVideo.filename}</span>
              </h3>
              <button
                className="icon-button"
                onClick={() => setActiveModalVideo(null)}
                aria-label="Close modal"
              >
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              <div>
                <div className="modal-video-wrap">
                  <video
                    controls
                    autoPlay
                    playsInline
                    src={activeModalVideo.source_url}
                  />
                </div>
                <div style={{ marginTop: "12px", display: "flex", gap: "10px" }}>
                  <a
                    className="button"
                    href={activeModalVideo.source_url}
                    download={activeModalVideo.filename}
                  >
                    Download MP4
                  </a>
                  <button
                    className="primary"
                    onClick={() => {
                      const cid = activeModalVideo.camera_id;
                      const vid = activeModalVideo.id;
                      const fname = activeModalVideo.filename;
                      setActiveModalVideo(null);
                      if (onInvestigate) {
                        onInvestigate("", cid, vid, fname);
                      } else {
                        window.location.pathname = "/investigation";
                      }
                    }}
                  >
                    Search in Investigation <ArrowUpRight size={14} />
                  </button>
                </div>
              </div>

              <div>
                <p className="eyebrow">FOOTAGE METADATA & METRICS</p>
                <dl style={{ margin: "14px 0" }}>
                  <div>
                    <dt>Camera</dt>
                    <dd>
                      {cameras.find((c) => c.id === activeModalVideo.camera_id)?.name || activeModalVideo.camera_id} (
                      <span className="mono">{activeModalVideo.camera_id}</span>)
                    </dd>
                  </div>
                  <div>
                    <dt>Duration</dt>
                    <dd>{time(activeModalVideo.duration)}</dd>
                  </div>
                  <div>
                    <dt>Resolution</dt>
                    <dd>
                      {activeModalVideo.width} × {activeModalVideo.height}
                    </dd>
                  </div>
                  <div>
                    <dt>Framerate</dt>
                    <dd>{activeModalVideo.fps.toFixed(2)} FPS</dd>
                  </div>
                  <div>
                    <dt>Codec</dt>
                    <dd>{activeModalVideo.codec}</dd>
                  </div>
                  <div>
                    <dt>File Size</dt>
                    <dd>{formatBytes(activeModalVideo.size)}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>
                      <span className={`status ${activeModalVideo.status === "READY" ? "ready" : ""}`}>
                        {activeModalVideo.status}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>Sampled Frames</dt>
                    <dd>{activeModalVideo.frames}</dd>
                  </div>
                  <div>
                    <dt>YOLO Detections</dt>
                    <dd>{activeModalVideo.objects}</dd>
                  </div>
                  <div>
                    <dt>Qdrant Vectors</dt>
                    <dd>{activeModalVideo.embeddings}</dd>
                  </div>
                  <div>
                    <dt>Uploaded</dt>
                    <dd>{new Date(activeModalVideo.created_at).toLocaleString()}</dd>
                  </div>
                </dl>

                <div className="note" style={{ fontSize: "11px", marginTop: "16px" }}>
                  All objects and background scenes in this recording have been indexed with 512-dimensional CLIP visual embeddings.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
