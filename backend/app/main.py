from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import Scenario
from backend.app.planner.core import build_plan
from backend.app.planner.exporters import to_geojson, to_kml

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

app = FastAPI(title="AeroMission Planner API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AeroMission Planner"}


@app.post("/api/plan")
def plan(scenario: Scenario):
    try:
        result = build_plan(scenario)
        return result.model_dump()
    except Exception as exc:  # keep demo resilient, but expose reason
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/export/geojson")
def export_geojson(plan_result: dict[str, Any]):
    return JSONResponse(to_geojson(plan_result), media_type="application/geo+json")


@app.post("/api/export/kml")
def export_kml(plan_result: dict[str, Any]):
    kml = to_kml(plan_result)
    return Response(kml, media_type="application/vnd.google-earth.kml+xml")
