export interface Camera {
  id: string;
  name: string;
  zone: string;
  footage_count: number;
  last_activity: string | null;
  live?: {
    status: string;
    segments: number;
    message: string;
    preview: boolean;
    started_at?: string;
    duration_minutes?: number;
    fps?: number;
    resolution?: string;
    elapsed_seconds?: number;
    stream_url?: string;
  };
}
export interface Video {
  id: string;
  filename: string;
  camera_id: string;
  duration: number;
  fps: number;
  width: number;
  height: number;
  frame_count: number;
  codec: string;
  size: number;
  status: string;
  progress: number;
  frames: number;
  objects: number;
  embeddings: number;
  error: string | null;
  created_at: string;
  source_url: string;
}
export interface Match {
  clip_start?: number;
  clip_end?: number;
  recorded_at?: string;
  evidence?: Evidence;
  video_id: string;
  camera_id: string;
  camera_name?: string;
  timestamp: number;
  start: number;
  end: number;
  frame_path: string;
  object_type: string;
  track_id: number | null;
  score?: number;
  cosine?: number;
  appearance?: string;
  filename: string;
  duration: number;
  matched_frames?: number;
  detected_objects?: any[];
  bounding_box?: number[];
  frame_width?: number;
  frame_height?: number;
  event_type?: string;
  matched_clues?: string[];
}

export interface ProgressionStep {
  clue: string;
  count: number;
}

export interface SearchResponse {
  id: string;
  query: string;
  clues: string[];
  progression: ProgressionStep[];
  results: Match[];
  object_filter: string | null;
  color_filter: string | null;
  candidates_truncated: boolean;
  score_explanation: string;
  notice: string;
}

export interface Evidence {
  summary: string;
  observations: string[];
  timeline: {timestamp: number; description: string}[];
  events: {timestamp: number; event_type: string; details: string}[];
  sample_count: number;
  source: string;
  limitation: string;
}
