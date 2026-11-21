"""SentinelAI Intelligence API Endpoints."""

import logging
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.storage import db
from backend.intelligence.risk_scoring import RiskScoringEngine
from backend.intelligence.route_reconstruction import RouteReconstructor
from backend.intelligence.copilot import InvestigationCopilot
from backend.intelligence.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

intelligence_router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


class RouteReconstructRequest(BaseModel):
    query: Optional[str] = None
    target_track_id: Optional[int] = None
    source_video_id: Optional[str] = None
    target_label: Optional[str] = "person"
    time_window_minutes: Optional[int] = 60
    min_affinity: Optional[float] = 0.65


class CopilotQueryRequest(BaseModel):
    query: str
    context_hours: Optional[int] = 24


class DossierGenerateRequest(BaseModel):
    case_title: str
    investigator_id: Optional[str] = "OFFICER-729"
    summary: Optional[str] = None
    route_data: Optional[Dict[str, Any]] = None
    alert_ids: Optional[List[str]] = None


@intelligence_router.get("/threat-status")
def get_threat_status():
    """Retrieve real-time global facility risk score and DEFCON posture."""
    return RiskScoringEngine.get_global_facility_threat()


@intelligence_router.post("/evaluate-entity-risk")
def evaluate_entity_risk(req: Dict[str, Any]):
    """Calculate composite risk score breakdown for a specific tracked target."""
    track_id = req.get("track_id", 1)
    alerts = db.rows("SELECT * FROM alerts WHERE track_id=?", (track_id,))
    dwell = float(req.get("dwell_seconds", 35.0))
    speed = float(req.get("max_speed", 0.28))
    return RiskScoringEngine.compute_entity_score(track_id, alerts, dwell, speed)


@intelligence_router.post("/route-reconstruct")
def reconstruct_route(req: RouteReconstructRequest, request: Request):
    """Reconstruct a suspect's trajectory across multiple disjoint camera views."""
    state = request.app.state
    if not hasattr(state, "reconstructor"):
        state.reconstructor = RouteReconstructor(state.store, state.embedder)

    # Encode textual target description if provided, or use default person anchor
    target_query = req.query or "a person in monitored sector"
    target_vector = state.embedder.encode_text(target_query)

    route_result = state.reconstructor.reconstruct_from_vector(
        target_vector=target_vector,
        time_window_minutes=req.time_window_minutes or 60,
        min_affinity=req.min_affinity or 0.65,
        target_label=req.target_label,
    )
    return route_result


@intelligence_router.post("/copilot/query")
def copilot_query(req: CopilotQueryRequest, request: Request):
    """Query the autonomous AI Investigation Copilot for tactical SITREP."""
    state = request.app.state
    if not hasattr(state, "copilot"):
        state.copilot = InvestigationCopilot(getattr(state, "search", None))

    return state.copilot.query_intelligence(req.query, req.context_hours or 24)


@intelligence_router.get("/copilot/explain/{alert_id}")
def copilot_explain_alert(alert_id: str, request: Request):
    """Explain threat rationale for a specific alert."""
    state = request.app.state
    if not hasattr(state, "copilot"):
        state.copilot = InvestigationCopilot(getattr(state, "search", None))

    return state.copilot.explain_threat(alert_id)


@intelligence_router.post("/reports/generate")
def generate_dossier(req: DossierGenerateRequest, request: Request):
    """Compile a forensic incident dossier with SHA-256 chain of custody."""
    state = request.app.state
    if not hasattr(state, "report_generator"):
        state.report_generator = ReportGenerator()

    return state.report_generator.generate_dossier(
        case_title=req.case_title,
        investigator_id=req.investigator_id or "OFFICER-729",
        summary=req.summary,
        route_data=req.route_data,
        alert_ids=req.alert_ids,
    )


@intelligence_router.get("/reports/{case_id}/download")
def download_dossier(case_id: str, request: Request):
    """Download compiled forensic dossier HTML/PDF."""
    state = request.app.state
    if not hasattr(state, "report_generator"):
        state.report_generator = ReportGenerator()

    file_path = state.report_generator.report_dir / f"{case_id}.html"
    if not file_path.exists():
        raise HTTPException(404, "Forensic dossier not found")

    return FileResponse(file_path, media_type="text/html", filename=f"{case_id}_dossier.html")


@intelligence_router.get("/cases")
def list_cases():
    """List all certified forensic investigation cases."""
    return db.rows("SELECT * FROM investigation_cases ORDER BY created_at DESC")
