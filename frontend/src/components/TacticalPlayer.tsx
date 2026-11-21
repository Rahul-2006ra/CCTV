import React, { useRef, useState, useEffect } from "react";
import { Play, Pause, Maximize2, Shield, Crosshair } from "lucide-react";

interface TacticalPlayerProps {
  src: string;
  detections?: Array<{
    bounding_box: [number, number, number, number];
    label: string;
    confidence: number;
    track_id?: number;
    threat_score?: number;
  }>;
  cameraName?: string;
  autoPlay?: boolean;
}

export const TacticalPlayer: React.FC<TacticalPlayerProps> = ({
  src,
  detections = [],
  cameraName = "CAM-FEED",
  autoPlay = false,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [currentTime, setCurrentTime] = useState(0);

  function togglePlay() {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  }

  return (
    <div
      style={{
        position: "relative",
        background: "#05080c",
        borderRadius: "6px",
        overflow: "hidden",
        border: "1px solid #1e293b",
        fontFamily: "'JetBrains Mono', monospace, sans-serif",
      }}
    >
      <video
        ref={videoRef}
        src={src}
        style={{ width: "100%", height: "auto", display: "block" }}
        onTimeUpdate={() => videoRef.current && setCurrentTime(videoRef.current.currentTime)}
        controls={false}
        loop
        playsInline
      />

      {/* Tactical HUD Header */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          padding: "8px 12px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%)",
          color: "#00ffc4",
          fontSize: "10px",
          pointerEvents: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Crosshair size={12} color="#00ffc4" />
          <span style={{ fontWeight: 700 }}>{cameraName} // ENCRYPTED LIVE FEED</span>
        </div>
        <div style={{ display: "flex", gap: "12px", color: "#94a3b8" }}>
          <span>T+{currentTime.toFixed(2)}s</span>
          <span style={{ color: "#00ffc4" }}>DEFENSE_C2_ACTIVE</span>
        </div>
      </div>

      {/* Simulated HUD Reticles for Detections */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: "none",
        }}
      >
        {detections.map((det, idx) => (
          <div
            key={idx}
            style={{
              position: "absolute",
              left: `${det.bounding_box[0] * 0.05}%`,
              top: `${det.bounding_box[1] * 0.05}%`,
              width: "80px",
              height: "120px",
              border: "1px dashed #00ffc4",
              borderRadius: "2px",
              boxShadow: "0 0 8px rgba(0, 255, 196, 0.4)",
            }}
          >
            <span
              style={{
                position: "absolute",
                top: "-16px",
                left: 0,
                background: "#00ffc4",
                color: "#05080c",
                fontSize: "8px",
                fontWeight: "bold",
                padding: "1px 4px",
                borderRadius: "2px",
              }}
            >
              #{det.track_id || idx} {det.label.toUpperCase()} {(det.confidence * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>

      {/* Bottom Control Bar */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: "6px 10px",
          background: "linear-gradient(0deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%)",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <button
          onClick={togglePlay}
          style={{
            background: "transparent",
            border: "none",
            color: "#e2e8f0",
            cursor: "pointer",
            padding: "4px",
            display: "flex",
          }}
        >
          {isPlaying ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <div style={{ flex: 1, height: "3px", background: "#334155", borderRadius: "2px" }}>
          <div style={{ width: `${(currentTime % 60) * 1.6}%`, height: "100%", background: "#00ffc4" }} />
        </div>
      </div>
    </div>
  );
};
