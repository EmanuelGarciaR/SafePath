"""
SafePath - Optimizador de Rutas (Backend)
"""
import json
from pathlib import Path
import math
import time
from typing import Tuple, List, Dict, Optional

import networkx as nx
import numpy as np
import pandas as pd
from shapely import wkt
try:
    from rtree import index as rtree_index
    RTREE_AVAILABLE = True
except Exception:
    RTREE_AVAILABLE = False


class SafePathRouter:
    """
    Clase para gestionar el grafo de calles y calcular rutas óptimas
    """

    def __init__(self, unified_data_path: Optional[str] = None):
        """
        Inicializa el router cargando los datos unificados

        Args:
            unified_data_path: Ruta al archivo unified_medellin_data.csv. Si es None,
                se intentará cargar desde <repo_root>/assets/unified_medellin_data.csv
        """
        print("=" * 60)
        print("SAFEPATH ROUTE OPTIMIZER - Inicializando")
        print("=" * 60)

        # Resolver ruta del CSV de forma robusta
        repo_root = Path(__file__).resolve().parents[1]
        default_path = repo_root / "assets" / "unified_medellin_data.csv"
        if unified_data_path is None:
            csv_path = default_path
        else:
            p = Path(unified_data_path)
            csv_path = p if p.is_absolute() else (repo_root / p)

        # Cargar datos
        print(f"Cargando datos unificados desde: {csv_path}")
        self.df = pd.read_csv(csv_path)

        # Convertir geometría de texto a objeto
        self.df["geometry"] = self.df["geometry"].apply(wkt.loads)

        # Crear el grafo dirigido (calles con dirección)
        self.G = nx.DiGraph()

        # Índices espaciales y aceleradores
        self._nodes_list = []  # type: ignore[var-annotated]
        self._node_to_id = {}
        self._id_to_node = {}
        self._node_rtree = None
        self._edge_rtree = None
        self._edge_bounds = {}
        self._min_combined_ratio = 0.0  # costo_comb/meters (límite inferior)
        self._min_risk_ratio = 0.0      # risk_score/meters (límite inferior)
        self._min_incident_ratio = 0.0  # incidents_count/meters (límite inferior)

        self._build_graph()
        self._build_spatial_indexes()

        print(
            f"✓ Grafo construido: {self.G.number_of_nodes()} nodos, {self.G.number_of_edges()} aristas"
        )
        print("=" * 60)

    def _parse_coordinate(self, coord_str: str) -> Tuple[float, float]:
        """
        Convierte string de coordenada a tupla (lon, lat)
        Ejemplo: "(-75.5728593, 6.2115169)" -> (-75.5728593, 6.2115169)
        """
        coord_str = coord_str.strip('()"')
        lon, lat = map(float, coord_str.split(","))
        return (lon, lat)

    def _build_graph(self):
        print("Construyendo grafo de calles...")

        min_combined_ratio = float("inf")
        min_risk_ratio = float("inf")
        min_inc_ratio = float("inf")
        for idx, row in self.df.iterrows():
            origin = self._parse_coordinate(row["origin"])
            destination = self._parse_coordinate(row["destination"])

            self.G.add_node(origin, pos=origin)
            self.G.add_node(destination, pos=destination)

            self.G.add_edge(
                origin,
                destination,
                # Atributos originales
                name=row["name"],
                length=row["length"],
                oneway=row["oneway"],
                geometry=row["geometry"],
                # Métricas de seguridad
                harassmentRisk=row["harassmentRisk"],
                cameras_count=row["cameras_count"],
                incidents_count=row["incidents_count"],
                incidents_severity=row["incidents_severity"],
                # Scores calculados
                risk_score=row["risk_score"],
                combined_cost=row["combined_cost"],
                # Pesos personalizados
                weight_distance=row["length"],
                weight_risk=row["risk_score"],
                weight_combined=row["combined_cost"],
                weight_incidents=(
                    row["incidents_count"]
                    if not pd.isna(row["incidents_count"]) else 0.0
                ),
            )

            if (idx + 1) % 10000 == 0:
                print(f"  Procesadas {idx + 1}/{len(self.df)} aristas...")

            # Preparar bounds por arista para filtrado espacial
            try:
                minx, miny, maxx, maxy = row["geometry"].bounds
            except Exception:
                # Fallback a bbox simple con extremos de origen/destino
                xs = [origin[0], destination[0]]
                ys = [origin[1], destination[1]]
                minx, maxx = min(xs), max(xs)
                miny, maxy = min(ys), max(ys)
            self._edge_bounds[idx] = (minx, miny, maxx, maxy)

            # Calcular razones mínimas por metro (para heurística A*)
            length = float(row.get("length", 0) or 0)
            combined = float(row.get("combined_cost", 0) or 0)
            risk_score = float(row.get("risk_score", 0) or 0)
            incidents_cnt = row.get("incidents_count", 0)
            try:
                incidents_cnt = float(incidents_cnt)
            except Exception:
                incidents_cnt = 0.0
            if length > 0:
                ratio = combined / length
                if ratio > 0 and ratio < min_combined_ratio:
                    min_combined_ratio = ratio
                r_ratio = risk_score / length
                if r_ratio > 0 and r_ratio < min_risk_ratio:
                    min_risk_ratio = r_ratio
                i_ratio = incidents_cnt / length
                if i_ratio > 0 and i_ratio < min_inc_ratio:
                    min_inc_ratio = i_ratio

        self._min_combined_ratio = 0.0 if min_combined_ratio == float("inf") else min_combined_ratio
        self._min_risk_ratio = 0.0 if min_risk_ratio == float("inf") else min_risk_ratio
        self._min_incident_ratio = 0.0 if min_inc_ratio == float("inf") else min_inc_ratio

        # Capturar listado de nodos para índice espacial
        self._nodes_list = list(self.G.nodes())
        for i, n in enumerate(self._nodes_list):
            self._node_to_id[n] = i
            self._id_to_node[i] = n

    def _build_spatial_indexes(self):
        """Construye índices espaciales para nodos y aristas si RTree está disponible."""
        if RTREE_AVAILABLE:
            # Índice para nodos
            p = rtree_index.Property()
            p.buffering_capacity = 8_192
            self._node_rtree = rtree_index.Index(properties=p)
            for i, (lon, lat) in enumerate(self._nodes_list):
                self._node_rtree.insert(i, (lon, lat, lon, lat))

            # Índice para aristas (por fila del DataFrame)
            p2 = rtree_index.Property()
            p2.buffering_capacity = 8_192
            self._edge_rtree = rtree_index.Index(properties=p2)
            for row_idx, bbox in self._edge_bounds.items():
                self._edge_rtree.insert(int(row_idx), bbox)
        else:
            print("(Aviso) RTree no disponible: se usarán búsquedas lineales (más lentas)")

    def find_nearest_node(self, lon: float, lat: float) -> Tuple[float, float]:
        """Encuentra el nodo más cercano usando RTree si está disponible (fallback lineal)."""
        if self._node_rtree is not None:
            # Buscar el id más cercano y validar distancia exacta
            try:
                nearest_ids = list(self._node_rtree.nearest((lon, lat, lon, lat), 5))
            except Exception:
                nearest_ids = []
            best = None
            best_d = float("inf")
            for nid in nearest_ids:
                n = self._id_to_node.get(int(nid))
                if not n:
                    continue
                d = (n[0] - lon) ** 2 + (n[1] - lat) ** 2
                if d < best_d:
                    best_d = d
                    best = n
            if best is not None:
                return best

        # Fallback lineal
        min_dist = float("inf")
        nearest = None
        for node in self._nodes_list:
            dist = (node[0] - lon) ** 2 + (node[1] - lat) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest

    def _degrees_buffer(self, meters: float, lat_ref: float) -> Tuple[float, float]:
        """Convierte un buffer en metros a grados (dx, dy) aproximados."""
        dy = meters / 111_000.0
        dx = meters / (111_000.0 * max(0.1, math.cos(math.radians(lat_ref))))
        return dx, dy

    def _edges_in_bbox(self, bbox: Tuple[float, float, float, float]) -> List[int]:
        """Devuelve índices de filas (aristas) cuyo bbox intersecta el bbox dado."""
        minx, miny, maxx, maxy = bbox
        if self._edge_rtree is not None:
            return list(self._edge_rtree.intersection((minx, miny, maxx, maxy)))
        # Fallback lineal
        out = []
        for ridx, (ex1, ey1, ex2, ey2) in self._edge_bounds.items():
            if not (ex2 < minx or ex1 > maxx or ey2 < miny or ey1 > maxy):
                out.append(int(ridx))
        return out

    def _build_temp_graph_for_bbox(self, bbox: Tuple[float, float, float, float]) -> nx.DiGraph:
        """Construye un grafo temporal con solo aristas que intersectan el bbox dado."""
        Gt = nx.DiGraph()
        candidate_rows = self._edges_in_bbox(bbox)
        if not candidate_rows:
            return Gt
        # Añadir aristas candidatas
        for ridx in candidate_rows:
            row = self.df.iloc[int(ridx)]
            origin = self._parse_coordinate(row["origin"])
            destination = self._parse_coordinate(row["destination"])
            Gt.add_node(origin, pos=origin)
            Gt.add_node(destination, pos=destination)
            Gt.add_edge(
                origin,
                destination,
                name=row["name"],
                length=row["length"],
                oneway=row["oneway"],
                geometry=row["geometry"],
                harassmentRisk=row["harassmentRisk"],
                cameras_count=row["cameras_count"],
                incidents_count=row["incidents_count"],
                incidents_severity=row["incidents_severity"],
                risk_score=row["risk_score"],
                combined_cost=row["combined_cost"],
                weight_distance=row["length"],
                weight_risk=row["risk_score"],
                weight_combined=row["combined_cost"],
                weight_incidents=(row["incidents_count"] if not pd.isna(row["incidents_count"]) else 0.0),
            )
        return Gt

    def calculate_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        optimization: str = "combined",
        algorithm: str = "dijkstra",
    ) -> Dict:
        print(f"\n{'=' * 60}")
        print(f"Calculando ruta con {algorithm.upper()} - Optimización: {optimization}")
        print(f"{'=' * 60}")

        start_node = self.find_nearest_node(origin[0], origin[1])
        end_node = self.find_nearest_node(destination[0], destination[1])

        print(f"Nodo inicial: {start_node}")
        print(f"Nodo final: {end_node}")

        opt_map = {
            "distance": "weight_distance",
            "risk": "weight_risk",
            "combined": "weight_combined",
            "incidents": "weight_incidents",
            "incident": "weight_incidents",
            "incidentes": "weight_incidents",
        }
        weight_attr = opt_map.get(optimization, f"weight_{optimization}")

        # Métricas de rendimiento
        start_time = time.time()
        nodes_explored = 0

        try:
            # Subgrafo por corredor (acota la búsqueda)
            # bbox entre origen y destino ampliado por margen en metros
            minx = min(start_node[0], end_node[0])
            maxx = max(start_node[0], end_node[0])
            miny = min(start_node[1], end_node[1])
            maxy = max(start_node[1], end_node[1])
            straight_m = math.sqrt((end_node[0]-start_node[0])**2 + (end_node[1]-start_node[1])**2) * 111_000
            margin_m = max(300.0, straight_m * 0.25)
            dx, dy = self._degrees_buffer(margin_m, (start_node[1]+end_node[1])/2.0)

            attempt = 0
            path = None
            cost = None
            G_used = None
            while attempt < 3 and path is None:
                bbox = (minx-dx, miny-dy, maxx+dx, maxy+dy)
                Gc = self._build_temp_graph_for_bbox(bbox)

                # Asegurar presencia de nodos; si faltan, expandir margen
                if (start_node not in Gc) or (end_node not in Gc):
                    attempt += 1
                    dx *= 1.5
                    dy *= 1.5
                    continue

                # Heurística admisible mejorada (data-driven)
                def h(n1, n2):
                    # metros en línea recta
                    d = math.sqrt((n1[0]-n2[0])**2 + (n1[1]-n2[1])**2) * 111_000
                    if weight_attr == "weight_distance":
                        return d
                    elif weight_attr == "weight_combined" and self._min_combined_ratio > 0:
                        return d * self._min_combined_ratio
                    elif weight_attr == "weight_risk":
                        # Usar razón mínima observada (riesgo/meters) como cota inferior
                        if self._min_risk_ratio > 0:
                            return d * self._min_risk_ratio
                        # Fallback conservador si no hay dato
                        return d * 0.0001
                    elif weight_attr == "weight_incidents":
                        if self._min_incident_ratio > 0:
                            return d * self._min_incident_ratio
                        # Fallback muy pequeño
                        return d * 0.00001
                    else:
                        return 0.0

                # Elegir algoritmo
                if algorithm == "dijkstra":
                    path = nx.dijkstra_path(Gc, start_node, end_node, weight=weight_attr)
                    cost = nx.dijkstra_path_length(Gc, start_node, end_node, weight=weight_attr)
                    G_used = Gc
                    nodes_explored = Gc.number_of_nodes()
                elif algorithm == "astar":
                    path = nx.astar_path(Gc, start_node, end_node, heuristic=h, weight=weight_attr)
                    cost = nx.astar_path_length(Gc, start_node, end_node, heuristic=h, weight=weight_attr)
                    G_used = Gc
                    nodes_explored = Gc.number_of_nodes()
                elif algorithm == "bellman_ford":
                    path = nx.bellman_ford_path(Gc, start_node, end_node, weight=weight_attr)
                    cost = nx.bellman_ford_path_length(Gc, start_node, end_node, weight=weight_attr)
                    G_used = Gc
                    nodes_explored = Gc.number_of_nodes()
                else:
                    raise ValueError(f"Algoritmo '{algorithm}' no reconocido")

                attempt += 1

            # Si no se obtuvo ruta en subgrafo tras varios intentos, usar grafo completo como fallback
            if path is None:
                G_used = self.G
                nodes_explored = self.G.number_of_nodes()
                if algorithm == "dijkstra":
                    path = nx.dijkstra_path(self.G, start_node, end_node, weight=weight_attr)
                    cost = nx.dijkstra_path_length(self.G, start_node, end_node, weight=weight_attr)
                elif algorithm == "astar":
                    def h_full(n1, n2):
                        d = math.sqrt((n1[0]-n2[0])**2 + (n1[1]-n2[1])**2) * 111_000
                        if weight_attr == "weight_distance":
                            return d
                        elif weight_attr == "weight_combined" and self._min_combined_ratio > 0:
                            return d * self._min_combined_ratio
                        elif weight_attr == "weight_risk":
                            if self._min_risk_ratio > 0:
                                return d * self._min_risk_ratio
                            return d * 0.0001
                        elif weight_attr == "weight_incidents":
                            if self._min_incident_ratio > 0:
                                return d * self._min_incident_ratio
                            return d * 0.00001
                        return 0.0
                    path = nx.astar_path(self.G, start_node, end_node, heuristic=h_full, weight=weight_attr)
                    cost = nx.astar_path_length(self.G, start_node, end_node, heuristic=h_full, weight=weight_attr)
                elif algorithm == "bellman_ford":
                    path = nx.bellman_ford_path(self.G, start_node, end_node, weight=weight_attr)
                    cost = nx.bellman_ford_path_length(self.G, start_node, end_node, weight=weight_attr)
                else:
                    raise ValueError(f"Algoritmo '{algorithm}' no reconocido")

            stats = self._calculate_route_stats(path, G_used)

            # Calcular tiempo de ejecución
            execution_time = time.time() - start_time

            print(f"\n✓ Ruta encontrada!")
            print(f"  - Nodos en la ruta: {len(path)}")
            print(f"  - Distancia total: {stats['total_distance']:.2f} metros")
            print(f"  - Riesgo promedio: {stats['avg_risk']:.4f}")
            print(f"  - Cámaras en ruta: {stats['total_cameras']}")
            print(f"  - Incidentes en ruta: {stats['total_incidents']}")
            print(f"  - Costo {optimization}: {cost:.4f}")
            print(f"  - Tiempo de ejecución: {execution_time*1000:.2f} ms")
            print(f"  - Nodos explorados: {nodes_explored}")

            return {
                "path": path,
                "cost": cost,
                "optimization": optimization,
                "algorithm": algorithm,
                "statistics": stats,
                "edges": self._get_edge_details(path, G_used),
                "performance": {
                    "execution_time_ms": float(execution_time * 1000),
                    "nodes_explored": int(nodes_explored),
                    "nodes_in_path": int(len(path)),
                }
            }

        except nx.NetworkXNoPath:
            print("✗ No se encontró ruta entre los puntos especificados")
            return None
        except Exception as e:
            print(f"✗ Error al calcular ruta: {str(e)}")
            return None

    def _calculate_route_stats(self, path: List[Tuple[float, float]], Gref: Optional[nx.DiGraph] = None) -> Dict:
        G = Gref or self.G
        total_distance = 0
        total_risk = 0
        total_cameras = 0
        total_incidents = 0
        edge_count = 0

        for i in range(len(path) - 1):
            edge_data = G[path[i]][path[i + 1]]
            total_distance += edge_data["length"]
            total_risk += edge_data["risk_score"]
            total_cameras += edge_data["cameras_count"]
            total_incidents += edge_data["incidents_count"]
            edge_count += 1

        # Convertir explícitamente a tipos nativos Python para evitar numpy.*
        return {
            "total_distance": float(total_distance),
            "avg_risk": float(total_risk / edge_count if edge_count > 0 else 0.0),
            "total_cameras": int(total_cameras),
            "total_incidents": int(total_incidents),
            "num_segments": int(edge_count),
        }

    def _get_edge_details(self, path: List[Tuple[float, float]], Gref: Optional[nx.DiGraph] = None) -> List[Dict]:
        G = Gref or self.G
        edges = []
        for i in range(len(path) - 1):
            edge_data = G[path[i]][path[i + 1]]
            edges.append(
                {
                    "from": (float(path[i][0]), float(path[i][1])),
                    "to": (float(path[i + 1][0]), float(path[i + 1][1])),
                    "name": str(edge_data["name"]),
                    "length": float(edge_data["length"]),
                    "harassmentRisk": float(edge_data["harassmentRisk"]),
                    "cameras_count": int(edge_data["cameras_count"]),
                    "incidents_count": int(edge_data["incidents_count"]),
                    "risk_score": float(edge_data["risk_score"]),
                    "geometry": edge_data["geometry"].wkt,
                }
            )
        return edges

    def compare_routes(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> Dict:
        print("\n" + "=" * 60)
        print("COMPARACIÓN DE ESTRATEGIAS DE RUTA")
        print("=" * 60)

        results = {}
        for opt_type in ["distance", "risk", "combined"]:
            route = self.calculate_route(origin, destination, optimization=opt_type)
            if route:
                results[opt_type] = route
        return results

    def export_route_to_geojson(self, route: Dict, output_path: str):
        features = []
        for edge in route["edges"]:
            feature = {
                "type": "Feature",
                "geometry": wkt.loads(edge["geometry"]).__geo_interface__,
                "properties": {
                    "name": edge["name"],
                    "length": edge["length"],
                    "harassmentRisk": edge["harassmentRisk"],
                    "cameras_count": edge["cameras_count"],
                    "incidents_count": edge["incidents_count"],
                    "risk_score": edge["risk_score"],
                },
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "optimization": route["optimization"],
                "algorithm": route["algorithm"],
                "statistics": route["statistics"],
            },
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)
        print(f"\n✓ Ruta exportada a: {output_path}")


# Helper rápido
def find_optimal_route(
    origin_lon: float,
    origin_lat: float,
    dest_lon: float,
    dest_lat: float,
    optimization: str = "combined",
    algorithm: str = "dijkstra",
):
    router = SafePathRouter()  # usa ruta por defecto bajo assets/
    route = router.calculate_route(
        (origin_lon, origin_lat),
        (dest_lon, dest_lat),
        optimization=optimization,
        algorithm=algorithm,
    )
    return route


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("EJEMPLO: Calculando ruta de prueba")
    print("=" * 60)

    router = SafePathRouter()
    origin = (-75.5657, 6.2080)
    destination = (-75.5676, 6.2528)

    comparison = router.compare_routes(origin, destination)
    if "combined" in comparison:
        repo_root = Path(__file__).resolve().parents[1]
        router.export_route_to_geojson(
            comparison["combined"], str(repo_root / "assets" / "route_example.geojson")
        )

    print("\n" + "=" * 60)
    print("EJEMPLO COMPLETADO")
    print("=" * 60)
    print("\nPara usar el router en tu código:")
    print("  from backend.route_optimizer import SafePathRouter")
    print("  router = SafePathRouter()")
    print("  route = router.calculate_route(origin, destination, 'combined')")
