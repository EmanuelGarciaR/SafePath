"""
SafePath API - FastAPI service
"""
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .route_optimizer import SafePathRouter
import math
from typing import Any, Dict

app = FastAPI(title="SafePath API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar router una sola vez (ruta por defecto bajo repo_root/assets)
router = SafePathRouter()


class RouteRequest(BaseModel):
    origin_lon: float
    origin_lat: float
    dest_lon: float
    dest_lat: float
    optimization: str = "combined"
    algorithm: str = "dijkstra"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/route")
async def compute_route(
    origin_lon: float = Query(...),
    origin_lat: float = Query(...),
    dest_lon: float = Query(...),
    dest_lat: float = Query(...),
    optimization: str = Query("combined"),
    algorithm: str = Query("dijkstra"),
):
    result = router.calculate_route(
        (origin_lon, origin_lat),
        (dest_lon, dest_lat),
        optimization=optimization,
        algorithm=algorithm,
    )
    if not result:
        return {"type": "FeatureCollection", "features": []}

    from shapely import wkt as _wkt

    def to_float(x: Any) -> float:
        try:
            v = float(x)
            return 0.0 if math.isnan(v) else v
        except Exception:
            return 0.0

    def to_int(x: Any) -> int:
        try:
            if x is None:
                return 0
            # Detect NaN
            try:
                v = float(x)
                if math.isnan(v):
                    return 0
            except Exception:
                pass
            return int(x)
        except Exception:
            try:
                v = float(x)
                return 0 if math.isnan(v) else int(v)
            except Exception:
                return 0

    features = []
    for e in result["edges"]:
        geom = _wkt.loads(e["geometry"]).__geo_interface__
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "name": str(e["name"]),
                    "length": to_float(e["length"]),
                    "harassmentRisk": to_float(e["harassmentRisk"]),
                    "cameras_count": to_int(e["cameras_count"]),
                    "incidents_count": to_int(e["incidents_count"]),
                    "risk_score": to_float(e["risk_score"]),
                    "optimization": str(result["optimization"]),
                    "algorithm": str(result["algorithm"]),
                },
            }
        )

    # Sanitizar estadísticas y costo
    stats = result.get("statistics", {})
    safe_stats: Dict[str, Any] = {
        "total_distance": to_float(stats.get("total_distance", 0.0)),
        "avg_risk": to_float(stats.get("avg_risk", 0.0)),
        "total_cameras": to_int(stats.get("total_cameras", 0)),
        "total_incidents": to_int(stats.get("total_incidents", 0)),
        "num_segments": to_int(stats.get("num_segments", 0)),
    }

    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "statistics": safe_stats,
            "cost": to_float(result.get("cost", 0.0)),
            "optimization": str(result.get("optimization", "")),
            "algorithm": str(result.get("algorithm", "")),
        },
    }


if __name__ == "__main__":
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
