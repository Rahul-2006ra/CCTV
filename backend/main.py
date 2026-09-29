import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import DATA, ROOT
from backend.storage.db import init_db
from backend.embeddings.clip_engine import ClipEngine
from backend.detection.detector import Detector
from backend.vector_store.qdrant_store import VectorStore
from backend.processing.pipeline import Pipeline
from backend.search.search_engine import SearchEngine
from backend.api.routes import router
from backend.live import LiveManager

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app):
    init_db()
    app.state.embedder = ClipEngine()
    app.state.embedder.load()
    app.state.detector = Detector()
    app.state.store = VectorStore()
    app.state.pipeline = Pipeline(
        app.state.embedder, app.state.detector, app.state.store
    )
    app.state.search = SearchEngine(app.state.embedder, app.state.store)
    _ = app.state.search.surveillance_neutrals
    app.state.live = LiveManager(app.state.pipeline)
    yield
    app.state.live.close()
    app.state.pipeline.close()
    app.state.store.close()


app = FastAPI(title="CCTV Intelligence", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    # Camera URLs can contain passwords; never echo request inputs in errors.
    return JSONResponse(
        status_code=422,
        content={
            "detail": [{k: e[k] for k in ("loc", "msg", "type")} for e in exc.errors()]
        },
    )


app.mount(
    "/media/thumbnails", StaticFiles(directory=DATA / "thumbnails"), name="thumbnails"
)
app.mount("/media/clips", StaticFiles(directory=DATA / "clips"), name="clips")

# Serve built frontend in production (Single universal URL / port)
dist_dir = ROOT / "frontend" / "dist"
if dist_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        if full_path.startswith("api") or full_path.startswith("media"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = dist_dir / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(dist_dir / "index.html")


@app.exception_handler(Exception)
async def unexpected(request: Request, exc: Exception):
    logging.exception("Unhandled request failure", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "The operation failed. Check backend logs and System health."
        },
    )
