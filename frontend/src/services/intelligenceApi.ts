import { api } from "./api";
import type {
  ThreatStatus,
  ReconstructedRoute,
  CopilotResponse,
  InvestigationCase,
  AnalyticsOverview,
} from "../types/intelligence";

export const intelligenceApi = {
  getThreatStatus: () => api<ThreatStatus>("/intelligence/threat-status"),

  reconstructRoute: (params: {
    query?: string;
    target_track_id?: number;
    target_label?: string;
    time_window_minutes?: number;
    min_affinity?: number;
  }) =>
    api<ReconstructedRoute>("/intelligence/route-reconstruct", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  queryCopilot: (query: string, context_hours: number = 24) =>
    api<CopilotResponse>("/intelligence/copilot/query", {
      method: "POST",
      body: JSON.stringify({ query, context_hours }),
    }),

  explainAlert: (alertId: string) =>
    api<{ alert_id: string; explanation: string; severity: string }>(
      `/intelligence/copilot/explain/${alertId}`
    ),

  generateDossier: (params: {
    case_title: string;
    investigator_id?: string;
    summary?: string;
    route_data?: any;
    alert_ids?: string[];
  }) =>
    api<{ case_id: string; title: string; sha256_hash: string; download_url: string }>(
      "/intelligence/reports/generate",
      {
        method: "POST",
        body: JSON.stringify(params),
      }
    ),

  getCases: () => api<InvestigationCase[]>("/intelligence/cases"),

  getAnalyticsOverview: () => api<AnalyticsOverview>("/analytics/overview"),

  getHeatmaps: () => api<{ cameras: Record<string, any[]> }>("/analytics/heatmaps"),
};
