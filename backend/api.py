"""
SafePath API - FastAPI service
"""
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .route_optimizer import SafePathRouter

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

    features = []
    for e in result["edges"]:
        geom = _wkt.loads(e["geometry"]).__geo_interface__
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "name": e["name"],
                    "length": e["length"],
                    "harassmentRisk": e["harassmentRisk"],
                    "cameras_count": e["cameras_count"],
                    "incidents_count": e["incidents_count"],
                    "risk_score": e["risk_score"],
                    "optimization": result["optimization"],
                    "algorithm": result["algorithm"],
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "statistics": result["statistics"],
            "cost": result["cost"],
            "optimization": result["optimization"],
            "algorithm": result["algorithm"],
        },
    }


if __name__ == "__main__":
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
