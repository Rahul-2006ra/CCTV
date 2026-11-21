export type ThreatSeverity = "CRITICAL" | "HIGH" | "ELEVATED" | "GUARDED" | "NORMAL" | "LOW";

export interface ThreatStatus {
  global_risk_score: number;
  threat_level: ThreatSeverity;
  status_code: string;
  active_threats: number;
  highest_risk_camera: string;
  critical_incidents: number;
}

export interface RouteNode {
  step_order: number;
  camera_id: string;
  camera_name: string;
  video_id: string;
  track_id: number;
  entry_time: number;
  exit_time: number;
  dwell_seconds: number;
  action: string;
  confidence: number;
  risk_score: number;
  thumbnail_url?: string;
}

export interface ReconstructedRoute {
  entity_id: string;
  route: RouteNode[];
  total_cameras: number;
  first_seen: number;
  last_seen: number;
  max_risk_score: number;
  severity_level: ThreatSeverity;
}

export interface CopilotResponse {
  query: string;
  response: string;
  threat_level: ThreatSeverity;
  matched_events_count: number;
  recommendations: string[];
  related_alert_ids: string[];
}

export interface InvestigationCase {
  id: string;
  case_number: string;
  title: string;
  investigator_id: string;
  status: string;
  threat_level: ThreatSeverity;
  summary: string;
  hash_signature: string;
  pdf_report_path: string;
  created_at: string;
  closed_at?: string;
}

export interface CameraMetric {
  camera_id: string;
  name: string;
  total_alerts: number;
  high_severity_alerts: number;
  risk_score: number;
  status: string;
  fps: number;
}

export interface AnalyticsOverview {
  summary: {
    total_detections: number;
    total_alerts: number;
    active_investigations: number;
    monitored_sectors: number;
    mean_time_to_detect_ms: number;
    system_availability: string;
  };
  severity_distribution: Record<string, number>;
  camera_performance: CameraMetric[];
  temporal_trends: Array<{
    hour: string;
    threat_count: number;
    incursions: number;
  }>;
}
