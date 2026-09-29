import { useState, useEffect } from "react";
import {
  Search,
  ArrowUpRight,
  SlidersHorizontal,
  ScanLine,
  Plus,
  X,
  RotateCcw,
  Sparkles,
  ArrowRight,
  Check,
  Tag,
  Film,
} from "lucide-react";
import { post, time } from "../services/api";
import type { Camera, Match, ProgressionStep, SearchResponse, Video } from "../types";
import InvestigationView from "../components/InvestigationView";

const objects = [
  "person",
  "car",
  "truck",
  "bus",
  "motorcycle",
  "bicycle",
  "backpack",
  "handbag",
  "suitcase",
];

const colors = [
  "red",
  "orange",
  "yellow",
  "green",
  "cyan",
  "blue",
  "purple",
  "pink",
  "black",
  "white",
  "gray",
  "brown",
];

export default function Investigation({
  cameras,
  videos = [],
  initial,
  onInitialConsumed,
}: {
  cameras: Camera[];
  videos?: Video[];
  initial?: any;
  onInitialConsumed: () => void;
}) {
  const [query, setQuery] = useState(initial?.query || "");
  const [clues, setClues] = useState<string[]>(initial?.clues || []);
  const [newClueInput, setNewClueInput] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(
    initial && Array.isArray(initial.results) ? initial : null
  );
  const [selected, setSelected] = useState<Match | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [camera, setCamera] = useState(initial?.camera_id || "");
  const [targetVideoId, setTargetVideoId] = useState<string | null>(initial?.video_id || null);
  const [targetVideoFilename, setTargetVideoFilename] = useState<string | null>(initial?.video_filename || null);
  const [object, setObject] = useState("");
  const [color, setColor] = useState("");
  const [minimum, setMinimum] = useState(0.15);

  useEffect(() => {
    if (initial) {
      const vid = initial.video_id || null;
      const vfname = initial.video_filename || null;
      const cid = initial.camera_id || "";
      const q = initial.query || "";
      const initialClues = initial.clues?.length ? initial.clues : (q ? [q] : []);

      setTargetVideoId(vid);
      setTargetVideoFilename(vfname);
      if (cid) setCamera(cid);
      setQuery(q);
      setClues(initialClues);

      if (Array.isArray(initial.results)) {
        setResult(initial);
        onInitialConsumed();
      } else if (q.trim()) {
        void executeSearch(q, initialClues, vid, cid);
      } else {
        setResult(null);
        onInitialConsumed();
      }
    }
  }, [initial]);

  async function executeSearch(
    primaryQuery: string,
    clueChain: string[],
    overrideVideoId?: string | null,
    overrideCameraId?: string | null,
  ) {
    if (!primaryQuery.trim()) return;
    setBusy(true);
    setResult(null); // Wipe previous search results immediately
    setError("");
    setSelected(null);
    onInitialConsumed();

    const activeVid = overrideVideoId !== undefined ? overrideVideoId : targetVideoId;
    const activeCam = overrideCameraId !== undefined ? overrideCameraId : camera;

    try {
      const response: SearchResponse = await post("/search", {
        query: primaryQuery.trim(),
        clues: clueChain,
        camera_id: activeCam || null,
        video_id: activeVid || null,
        object_type: object || null,
        color: color || null,
        min_relevance: minimum,
      });

      setResult(response);
      setClues(response.clues || [primaryQuery]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // Initial search from form
  function handleMainSearch() {
    const trimmed = query.trim();
    if (!trimmed) return;
    setResult(null); // Wipe previous results immediately
    const chain = [trimmed];
    setClues(chain);
    void executeSearch(trimmed, chain);
  }

  // Add refinement clue
  function handleAddClue(e?: React.FormEvent) {
    if (e) e.preventDefault();
    const trimmed = newClueInput.trim();
    if (!trimmed) return;

    const base = clues.length > 0 ? clues[0] : query.trim() || trimmed;
    const updatedChain = [...clues, trimmed];
    setClues(updatedChain);
    setNewClueInput("");
    void executeSearch(base, updatedChain);
  }

  // Remove ANY clue from the pipeline (including Clue 1)
  function handleRemoveClue(indexToRemove: number) {
    const updatedChain = clues.filter((_, i) => i !== indexToRemove);
    if (updatedChain.length === 0) {
      // All clues removed: reset search completely so screen is clean
      setClues([]);
      setResult(null);
      setQuery("");
    } else {
      setClues(updatedChain);
      setQuery(updatedChain[0]);
      void executeSearch(updatedChain[0], updatedChain);
    }
  }

  // Reset refinements back to initial search
  function handleResetClues() {
    if (clues.length > 0) {
      const initialClue = clues[0];
      setClues([initialClue]);
      setQuery(initialClue);
      void executeSearch(initialClue, [initialClue]);
    } else {
      setResult(null);
      setClues([]);
      setQuery("");
    }
  }

  if (selected) {
    return (
      <InvestigationView
        key={`${selected.video_id}-${selected.start}-${selected.end}`}
        match={selected}
        query={result?.query}
        onClose={() => setSelected(null)}
      />
    );
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">WORKSPACE / PROGRESSIVE VISUAL RETRIEVAL</p>
          <h1>Progressive CCTV Investigation</h1>
          <p className="subtitle">
            Iteratively narrow suspect candidates using natural language visual clues.
          </p>
        </div>
        <span className="badge">
          <span className="dot" /> LOCAL AI INFERENCE
        </span>
      </div>

      {/* Video Selector Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
          padding: "12px 18px",
          marginBottom: "16px",
          borderRadius: "8px",
          background: targetVideoId
            ? "linear-gradient(135deg, rgba(82, 196, 26, 0.12), rgba(16, 28, 22, 0.8))"
            : "#151b1e",
          border: targetVideoId
            ? "1px solid rgba(82, 196, 26, 0.4)"
            : "1px solid #222d32",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Film size={18} color="var(--accent)" />
          <span style={{ fontSize: "13px", fontWeight: 600, color: "#d0d7de" }}>
            Investigating Video:
          </span>
          <select
            aria-label="Select video to investigate"
            value={targetVideoId || "all"}
            onChange={(e) => {
              const val = e.target.value;
              const vid = val === "all" ? null : val;
              const found = videos.find((v) => v.id === vid);
              setTargetVideoId(vid);
              setTargetVideoFilename(found ? found.filename : null);
              if (query.trim()) {
                void executeSearch(query.trim(), clues, vid);
              }
            }}
            style={{
              background: "#1c2428",
              border: "1px solid #37444c",
              color: "#fff",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer",
              outline: "none",
            }}
          >
            <option value="all">
              🌐 All Videos ({videos.filter((v) => v.status === "READY").length} ready)
            </option>
            {videos.map((v) => (
              <option key={v.id} value={v.id} disabled={v.status !== "READY"}>
                📹 {v.filename} ({time(v.duration)}) — {v.status === "READY" ? "Ready" : v.status}
              </option>
            ))}
          </select>
        </div>

        {targetVideoId ? (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                fontSize: "12px",
                color: "#a9dfbf",
                background: "rgba(82, 196, 26, 0.15)",
                padding: "3px 8px",
                borderRadius: "4px",
              }}
            >
              Scoped to: <strong>{targetVideoFilename || targetVideoId}</strong>
            </span>
            <button
              type="button"
              onClick={() => {
                setTargetVideoId(null);
                setTargetVideoFilename(null);
                if (query.trim()) {
                  void executeSearch(query.trim(), clues, null);
                }
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                background: "#222a2e",
                border: "1px solid #37444c",
                color: "#d0d7de",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "12px",
                cursor: "pointer",
              }}
              title="Search across all videos"
            >
              <X size={12} /> Clear focus
            </button>
          </div>
        ) : (
          <span style={{ fontSize: "12px", color: "#8c98a0" }}>
            Investigating across all indexed recordings. Pick a video above to focus.
          </span>
        )}
      </div>

      {/* Main Search Bar */}
      <section className="search-panel panel">
        <form
          className="search-box"
          onSubmit={(e) => {
            e.preventDefault();
            handleMainSearch();
          }}
        >
          <Search size={22} />
          <input
            aria-label="Search footage"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              targetVideoFilename
                ? `Search inside "${targetVideoFilename}" (e.g. 'red shirt', 'backpack', 'car')…`
                : "Start with a visual description (e.g. 'person in red shirt', 'white car', 'backpack')…"
            }
            maxLength={500}
          />
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setClues([]);
                setResult(null);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: "#8c98a0",
                cursor: "pointer",
                padding: "4px 8px",
                display: "flex",
                alignItems: "center",
              }}
              title="Clear search"
            >
              <X size={16} />
            </button>
          )}
          <button className="primary" disabled={busy || !query.trim()}>
            {busy ? "Searching…" : "Search footage"}
            <ArrowUpRight size={16} />
          </button>
        </form>

        <div className="suggestions">
          <span>SCENARIO SUGGESTIONS</span>
          {[
            "Find a person wearing a red shirt",
            "Find someone running",
            "Find an unattended backpack",
            "Find a white car",
            "Find two people fighting",
            "Find suspicious loitering",
            "Find night surveillance scene",
            "Find a person walking",
          ].map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuery(s);
                const chain = [s];
                setClues(chain);
                setResult(null);
                void executeSearch(s, chain);
              }}
              disabled={busy}
            >
              {s}
              <ArrowUpRight size={12} />
            </button>
          ))}
        </div>

        <div className="filters">
          <SlidersHorizontal size={15} />
          <label>
            Camera
            <select
              aria-label="Search camera filter"
              value={camera}
              onChange={(e) => setCamera(e.target.value)}
            >
              <option value="">All cameras</option>
              {cameras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Object
            <select value={object} onChange={(e) => setObject(e.target.value)}>
              <option value="">Any object</option>
              {objects.map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label>
            Color
            <select value={color} onChange={(e) => setColor(e.target.value)}>
              <option value="">Any color</option>
              {colors.map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label>
            Minimum relevance
            <input
              aria-label="Minimum relevance"
              className="number-input"
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={minimum}
              onChange={(e) => setMinimum(Number(e.target.value))}
            />
          </label>
        </div>
      </section>

      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}

      {/* PROGRESSIVE INVESTIGATION PIPELINE BAR */}
      {result && Array.isArray(result.results) && clues.length > 0 && (
        <section className="clues-pipeline-container">
          <div className="clues-pipeline-header">
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Sparkles size={14} color="var(--accent)" />
              PROGRESSIVE CLUES FUNNEL ({result.results?.length ?? 0} MATCHING CANDIDATES)
            </span>
            {clues.length > 1 && (
              <button
                className="text-button"
                onClick={handleResetClues}
                style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px" }}
              >
                <RotateCcw size={12} /> Reset to initial clue
              </button>
            )}
          </div>

          <div className="clues-pipeline-steps">
            {clues.map((clueText, index) => {
              const stepData = result.progression?.find(
                (p: ProgressionStep) => p.clue.toLowerCase() === clueText.toLowerCase()
              );
              const count = stepData?.count ?? (index === clues.length - 1 ? (result.results?.length ?? 0) : "—");

              return (
                <div key={`${clueText}-${index}`} style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                  <div className={`clue-chip ${index === clues.length - 1 ? "active" : ""}`}>
                    <span style={{ fontWeight: 600 }}>Clue {index + 1}:</span>
                    <span>"{clueText}"</span>
                    <span className="count-badge" title={`${count} candidates match at this stage`}>
                      {count} {typeof count === "number" && count === 1 ? "match" : "matches"}
                    </span>
                    <button
                      className="remove-btn"
                      onClick={() => handleRemoveClue(index)}
                      title={`Remove clue ${index + 1}: '${clueText}'`}
                      disabled={busy}
                    >
                      <X size={12} />
                    </button>
                  </div>
                  {index < clues.length - 1 && (
                    <ArrowRight size={14} className="clue-arrow" />
                  )}
                </div>
              );
            })}

            {/* Add Next Clue Form */}
            <ArrowRight size={14} className="clue-arrow" />
            <form onSubmit={handleAddClue} className="add-clue-form">
              <input
                placeholder="+ Add next clue (e.g. 'black pants', 'backpack')…"
                value={newClueInput}
                onChange={(e) => setNewClueInput(e.target.value)}
                disabled={busy}
              />
              <button
                type="submit"
                className="primary"
                disabled={busy || !newClueInput.trim()}
              >
                <Plus size={12} /> Refine
              </button>
            </form>
          </div>
        </section>
      )}

      {/* Results Header */}
      <div className="results-heading">
        <h3>
          {result && Array.isArray(result.results)
            ? `${result.results.length} matching events`
            : "Investigation results"}
        </h3>
        <span>
          {result
            ? "RANKED BY CLIP SIMILARITY & MULTI-SIGNAL ATTRIBUTES"
            : "SOURCE-VERIFIED · TEMPORALLY GROUPED"}
        </span>
      </div>

      {result && (
        <p className="muted" style={{ marginBottom: "16px" }}>
          {result.score_explanation}
          {result.object_filter && ` · Object filter: ${result.object_filter}`}
          {result.color_filter && ` · Color filter: ${result.color_filter}`}
        </p>
      )}

      {result?.candidates_truncated && (
        <div className="note">
          Showing the top 1,000 candidate samples. Narrow by camera or add progressive clues for tighter event coverage.
        </div>
      )}

      {/* Result Cards Grid */}
      {!result || !Array.isArray(result.results) || !result.results.length ? (
        <div className="empty panel">
          <ScanLine size={38} />
          <h3>
            {result
              ? "No matching footage found."
              : "Start with an initial search description."}
          </h3>
          <p>
            {result
              ? "Try adjusting your clue chain or relevance threshold. Only indexed footage is searched."
              : "Search for people, clothing, vehicles, accessories, and actions across your indexed footage recordings."}
          </p>
          <span>Upload footage and configure a virtual camera to begin.</span>
        </div>
      ) : (
        <div className="result-grid">
          {result.results.map((r: Match, i: number) => {
            const camName =
              cameras.find((c) => c.id === r.camera_id)?.name ||
              r.camera_name ||
              r.camera_id;

            return (
              <button
                className="result-card"
                key={`${r.video_id}-${r.start}-${i}`}
                onClick={() => setSelected(r)}
              >
                <div className="thumbnail">
                  <img
                    src={r.frame_path}
                    alt={`${r.object_type} at ${time(r.timestamp)}`}
                  />
                  <span className="camera-overlay">{camName}</span>
                  <span className="time-overlay">
                    {time(r.start)} – {time(r.end)}
                  </span>
                  {r.bounding_box && (
                    <div
                      className="bounding-box"
                      style={{
                        left: `${(r.bounding_box[0] / r.frame_width!) * 100}%`,
                        top: `${(r.bounding_box[1] / r.frame_height!) * 100}%`,
                        width: `${((r.bounding_box[2] - r.bounding_box[0]) / r.frame_width!) * 100}%`,
                        height: `${((r.bounding_box[3] - r.bounding_box[1]) / r.frame_height!) * 100}%`,
                      }}
                    />
                  )}
                </div>
                <div className="result-content">
                  <div>
                    <h3>
                      {r.object_type === "scene"
                        ? "Scene Match"
                        : r.object_type.charAt(0).toUpperCase() + r.object_type.slice(1)}
                    </h3>
                    <span className="relevance">
                      {r.score?.toFixed(3)} <small>score</small>
                    </span>
                  </div>

                  <p>
                    {r.appearance
                      ? `${r.appearance} appearance`
                      : "Visual scene similarity"}
                    {r.track_id != null && ` · Track ${r.track_id}`}
                  </p>

                  {/* Matched clues chips */}
                  {r.matched_clues && r.matched_clues.length > 0 && (
                    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", marginTop: "4px" }}>
                      {r.matched_clues.map((c, ci) => (
                        <span
                          key={ci}
                          style={{
                            background: "rgba(185, 219, 129, 0.15)",
                            color: "var(--accent)",
                            border: "1px solid rgba(185, 219, 129, 0.3)",
                            borderRadius: "3px",
                            padding: "1px 5px",
                            fontSize: "9px",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "3px",
                          }}
                        >
                          <Check size={8} /> {c}
                        </span>
                      ))}
                    </div>
                  )}

                  <footer>
                    <span>
                      {r.matched_frames} samples · {r.filename}
                    </span>
                    <ArrowUpRight size={17} />
                  </footer>
                </div>
              </button>
            );
          })}
        </div>
      )}

      <p className="footnote">
        Visual search supports investigation; it does not establish identity or
        intent. Action and relationship queries return approximate visual
        matches.
      </p>
    </>
  );
}
