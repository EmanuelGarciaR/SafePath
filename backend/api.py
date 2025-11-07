"""
SafePath API - FastAPI service
"""
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .route_optimizer import SafePathRouter
from .advanced_routing import AdvancedRouter
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

# Cargar router con algoritmos avanzados
router = AdvancedRouter()


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


@app.get("/compare")
async def compare_routes(
    origin_lon: float = Query(...),
    origin_lat: float = Query(...),
    dest_lon: float = Query(...),
    dest_lat: float = Query(...),
    optimization: str = Query("combined"),
    algorithms: str = Query("dijkstra,greedy,branch_and_bound"),  # Comma-separated list
):
    """
    Compare multiple routing algorithms simultaneously.
    Returns a GeoJSON FeatureCollection with routes from each algorithm.
    """
    algo_list = [a.strip() for a in algorithms.split(",")]
    results = []
    
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
    
    for algo in algo_list:
        try:
            # Calculate route for this algorithm
            result = None
            if algo in ["greedy", "backtracking", "branch_and_bound"]:
                try:
                    if algo == "greedy":
                        result = router.greedy_route((origin_lon, origin_lat), (dest_lon, dest_lat), optimization)
                    elif algo == "backtracking":
                        result = router.backtracking_route((origin_lon, origin_lat), (dest_lon, dest_lat), optimization)
                    elif algo == "branch_and_bound":
                        result = router.branch_and_bound_route((origin_lon, origin_lat), (dest_lon, dest_lat), optimization)
                except Exception as e_alg:
                    print(f"⚠ {algo} failed: {e_alg}")
                    result = None

                # Fallback to Dijkstra if advanced algorithm fails
                if result is None:
                    try:
                        print(f"⚠ {algo.upper()} no encontró ruta. Usando Dijkstra como fallback en /compare...")
                        result = router.calculate_route(
                            (origin_lon, origin_lat),
                            (dest_lon, dest_lat),
                            optimization=optimization,
                            algorithm="dijkstra",
                        )
                        if result:
                            result["note"] = f"fallback: Dijkstra"
                            # Mantener el nombre original del algoritmo para asignación de colores/posiciones
                            result["algorithm"] = algo
                    except Exception as e_fb:
                        print(f"✗ Fallback Dijkstra también falló para {algo}: {e_fb}")
                        result = None
            else:
                result = router.calculate_route(
                    (origin_lon, origin_lat),
                    (dest_lon, dest_lat),
                    optimization=optimization,
                    algorithm=algo,
                )
            
            if result:
                # Build features for this algorithm
                features = []
                for e in result["edges"]:
                    geom = _wkt.loads(e["geometry"]).__geo_interface__
                    features.append({
                        "type": "Feature",
                        "geometry": geom,
                        "properties": {
                            "name": str(e["name"]),
                            "length": to_float(e["length"]),
                            "harassmentRisk": to_float(e["harassmentRisk"]),
                            "cameras_count": to_int(e["cameras_count"]),
                            "incidents_count": to_int(e["incidents_count"]),
                            "risk_score": to_float(e["risk_score"]),
                            "algorithm": algo,
                        },
                    })
                
                stats = result.get("statistics", {})
                results.append({
                    "algorithm": algo,
                    "features": features,
                    "statistics": {
                        "total_distance": to_float(stats.get("total_distance", 0.0)),
                        "avg_risk": to_float(stats.get("avg_risk", 0.0)),
                        "total_cameras": to_int(stats.get("total_cameras", 0)),
                        "total_incidents": to_int(stats.get("total_incidents", 0)),
                        "num_segments": to_int(stats.get("num_segments", 0)),
                    },
                    "cost": to_float(result.get("cost", 0.0)),
                    "note": result.get("note", ""),
                })
        except Exception as e:
            print(f"⚠ Error calculating route with {algo}: {e}")
            # Continue with other algorithms
    
    return {
        "type": "Comparison",
        "optimization": optimization,
        "routes": results
    }


@app.get("/route")
async def compute_route(
    origin_lon: float = Query(...),
    origin_lat: float = Query(...),
    dest_lon: float = Query(...),
    dest_lat: float = Query(...),
    optimization: str = Query("combined"),
    algorithm: str = Query("dijkstra"),
):
    result = None
    
    # Use advanced algorithms if specified
    if algorithm in ["greedy", "backtracking", "branch_and_bound"]:
        try:
            if algorithm == "greedy":
                result = router.greedy_route((origin_lon, origin_lat), (dest_lon, dest_lat), optimization)
            elif algorithm == "backtracking":
                result = router.backtracking_route((origin_lon, origin_lat), (dest_lon, dest_lat), optimization)
            elif algorithm == "branch_and_bound":
                result = router.branch_and_bound_route((origin_lon, origin_lat), (dest_lon, dest_lat), optimization)
        except Exception as e:
            print(f"⚠ Algoritmo {algorithm} falló: {e}. Intentando con A* como fallback...")
            result = None
        
        # Fallback to Dijkstra if advanced algorithm failed
        if result is None:
            print(f"⚠ {algorithm.upper()} no encontró ruta. Usando Dijkstra como fallback...")
            try:
                result = router.calculate_route(
                    (origin_lon, origin_lat),
                    (dest_lon, dest_lat),
                    optimization=optimization,
                    algorithm="dijkstra",
                )
                if result:
                    result["algorithm"] = f"{algorithm}_fallback_dijkstra"
                    result["note"] = f"fallback: Dijkstra"
            except Exception as e2:
                print(f"✗ Fallback Dijkstra también falló: {e2}")
    else:
        # Standard algorithms (dijkstra, astar, bellman_ford)
        # Dijkstra is the recommended default for best performance
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
