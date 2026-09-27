import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Download,
  ExternalLink,
  Film,
  LoaderCircle,
} from "lucide-react";
import { api, post, time } from "../services/api";
import type { Evidence, Match } from "../types";

export default function InvestigationView({
  match,
  onClose,
  query,
}: {
  match: Match;
  onClose: () => void;
  query?: string;
}) {
  const [clip, setClip] = useState<any>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [current, setCurrent] = useState(match.timestamp),
    [original, setOriginal] = useState(false);
  const [start, setStart] = useState(match.clip_start ?? match.start);
  const [end, setEnd] = useState(match.clip_end ?? Math.min(match.duration, Math.max(match.end, match.start + 1)));
  const [context, setContext] = useState(false);
  const [report, setReport] = useState<Evidence | undefined>(match.evidence);
  const sequence = useRef(0);
  const player = useRef<HTMLVideoElement>(null);
  const pending = useRef<{key: string; promise: Promise<any>} | null>(null);
  const pendingSeek = useRef<number | null>(null);
  async function generate() {
    if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start || end > match.duration) {
      setError("Choose a start and end inside the recording, with end after start."); return;
    }
    const request = ++sequence.current;
    setBusy(true);
    setError("");
    setClip(null);
    setReport(undefined);
    try {
      const key = JSON.stringify([match.video_id, start, end, context]);
      if (pending.current?.key !== key)
        pending.current = {key, promise: post("/clips", {
          video_id: match.video_id,
          start,
          end,
          context,
        })};
      const generated = await pending.current.promise;
      if (sequence.current !== request) return;
      setClip(generated);
      setCurrent(start);
      setOriginal(false);
      const evidence = await api<Evidence>(`/videos/${match.video_id}/evidence?start=${start}&end=${end}`);
      if (sequence.current === request) setReport(evidence);
    } catch (e) {
      if (sequence.current === request) setError((e as Error).message);
    } finally {
      if (sequence.current === request) {pending.current = null; setBusy(false);}
    }
  }
  useEffect(() => {
    void generate();
    return () => {sequence.current += 1;};
  }, [match.video_id, match.start, match.end]);
  const offset = original ? 0 : clip?.start || 0;
  function seek(value: number) {
    if (!original && clip && (value < clip.start || value > clip.end)) {
      pendingSeek.current = value;
      setOriginal(true);
      return;
    }
    if (player.current) {
      player.current.currentTime = Math.max(0, value - offset);
      setCurrent(value);
    }
  }
  return (
    <section className="investigation-view">
      <button className="text-button" onClick={onClose}>
        <ArrowLeft size={15} /> Back to results
      </button>
      <div className="section-heading">
        <div>
          <p className="eyebrow">EVIDENCE REVIEW / {match.camera_id}</p>
          <h2>{match.event_type || "Matching footage & evidence report"}</h2>
          {query && <p className="subtitle">Search description: {query}</p>}
          {report && <p className="subtitle">{report.summary}</p>}
        </div>
        <span className="badge">SOURCE TIME {time(match.timestamp)}</span>
      </div>
      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}
      <div className="review-grid">
        <div className="panel player-panel">
          <div className="panel-label">
            <span>{match.filename}</span>
            <span>{original ? "ORIGINAL" : "SELECTED CLIP"}</span>
          </div>
          {clip || original ? (
            <video
              key={original ? "source" : clip.id}
              ref={player}
              controls
              playsInline
              preload="auto"
              src={original ? `/api/videos/${match.video_id}/source` : clip.url}
              onLoadedMetadata={() => {
                seek(pendingSeek.current ?? (original ? match.timestamp : clip.start));
                pendingSeek.current = null;
              }}
              onTimeUpdate={() =>
                setCurrent((player.current?.currentTime || 0) + offset)
              }
              onError={() =>
                setError(
                  "Browser could not play this video. Generate an H.264 context clip for compatible playback.",
                )
              }
            />
          ) : (
            <div className="player-empty">
              <LoaderCircle className="spin" />
              <p>{busy ? "Preparing your playable clip…" : "Choose an interval and generate a clip."}</p>
            </div>
          )}
          <div className="player-controls">
            <button
              onClick={() => {
                setOriginal(true);
                setError("");
              }}
            >
              <ExternalLink size={14} /> Open Original
            </button>
            <button onClick={generate} disabled={busy}>
              <Film size={14} />
              {busy ? "Generating…" : "Generate Clip"}
            </button>
            {clip && (
              <a
                className="button"
                href={`/api/clips/${clip.id}?download=true`}
                download
              >
                <Download size={14} /> Download clip
              </a>
            )}
          </div>
          <div className="clip-editor">
            <label>Clip start (seconds)<input aria-label="Clip start (seconds)" type="number" min={0} max={match.duration} step="0.1" value={start} disabled={busy} onChange={e => setStart(Number(e.target.value))}/></label>
            <label>Clip end (seconds)<input aria-label="Clip end (seconds)" type="number" min={0} max={match.duration} step="0.1" value={end} disabled={busy} onChange={e => setEnd(Number(e.target.value))}/></label>
            <label className="context-toggle"><input type="checkbox" checked={context} disabled={busy} onChange={e => setContext(e.target.checked)}/>Include surrounding context</label>
            <p className="muted">Adjust the interval, then Generate Clip. The download contains the generated boundaries shown below.</p>
          </div>
          <div className="timeline">
            <div className="panel-label">
              <span>SOURCE TIMELINE</span>
              <strong>
                {time(current)} / {time(match.duration)}
              </strong>
            </div>
            <div className="timeline-track">
              <span
                className="event-band"
                style={{
                  left: `${(match.start / match.duration) * 100}%`,
                  width: `${Math.max(1, ((match.end - match.start) / match.duration) * 100)}%`,
                }}
              />
              <input
                aria-label="Source timeline"
                type="range"
                min={0}
                max={match.duration}
                step="0.1"
                value={current}
                onChange={(e) => seek(Number(e.target.value))}
              />
            </div>
            <div className="ticks">
              <span>{time(0)}</span>
              <span>{time(match.duration / 2)}</span>
              <span>{time(match.duration)}</span>
            </div>
            <p className="muted">
              Highlighted interval: {time(match.start)} – {time(match.end)}.
              Times are offsets from the source video.
            </p>
          </div>
        </div>
        <aside className="panel details">
          <p className="eyebrow">INVESTIGATION DETAILS</p>
          <dl>
            {Object.entries({
              Camera: match.camera_id,
              Video: match.filename,
              "Event interval": `${time(match.start)} – ${time(match.end)}`,
              "Best match": time(match.timestamp),
              Object: match.object_type,
              "Track ID": match.track_id ?? "Unavailable",
              Appearance: match.appearance || "Not assessed",
              Relevance: match.score?.toFixed(3) ?? "Rule-based event",
              "CLIP cosine": match.cosine?.toFixed(3) ?? "Not applicable",
              "Matched samples": match.matched_frames ?? "Not applicable",
              "Clip boundaries": clip
                ? `${time(clip.start, true)} – ${time(clip.end, true)}`
                : "Generating…",
            }).map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          <div className="note">
            Relevance is a retrieval score, not a probability. Review the
            original footage before drawing conclusions.
          </div>
          {match.detected_objects && (
            <>
              <p className="eyebrow">DETECTIONS AT MATCH</p>
              {match.detected_objects.map((d, i) => (
                <div key={i} className="detection">
                  <span>
                    {d.label} · track {d.track_id ?? "—"}
                  </span>
                  <span>{d.confidence.toFixed(3)}</span>
                </div>
              ))}
            </>
          )}
        </aside>
      </div>
      {report && <section className="panel evidence-report">
        <p className="eyebrow">EVIDENCE DESCRIPTION</p>
        <h3>What the footage shows</h3>
        <p>{report.summary}</p>
        {match.recorded_at && <p>Live recording start (approximate computer time): {new Date(match.recorded_at).toLocaleString()}</p>}
        {report.observations.length > 0 && <ul>{report.observations.map((text, i) => <li key={i}>{text}</li>)}</ul>}
        {report.events.length > 0 && <><h3>Event signals</h3>{report.events.map((event, i) => <p key={i}>{time(event.timestamp)} · {event.event_type}: {event.details}</p>)}</>}
        <details><summary>Frame-by-frame observations ({report.sample_count} samples)</summary>{report.timeline.map((entry, i) => <div className="detection" key={i}><strong>{time(entry.timestamp)}</strong><span>{entry.description}</span></div>)}</details>
        <p className="note">{report.limitation}</p>
      </section>}
    </section>
  );
}
