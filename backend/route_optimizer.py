"""
SafePath - Optimizador de Rutas (Backend)
"""
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional

import networkx as nx
import numpy as np
import pandas as pd
from shapely import wkt


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

        self._build_graph()

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

    def find_nearest_node(self, lon: float, lat: float) -> Tuple[float, float]:
        min_dist = float("inf")
        nearest = None
        for node in self.G.nodes():
            dist = np.sqrt((node[0] - lon) ** 2 + (node[1] - lat) ** 2)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        return nearest

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

        try:
            if algorithm == "dijkstra":
                path = nx.dijkstra_path(self.G, start_node, end_node, weight=weight_attr)
                cost = nx.dijkstra_path_length(
                    self.G, start_node, end_node, weight=weight_attr
                )
            elif algorithm == "astar":
                def heuristic(node1, node2):
                    return (
                        np.sqrt((node1[0] - node2[0]) ** 2 + (node1[1] - node2[1]) ** 2)
                        * 111000
                    )

                path = nx.astar_path(
                    self.G, start_node, end_node, heuristic=heuristic, weight=weight_attr
                )
                cost = nx.astar_path_length(
                    self.G, start_node, end_node, heuristic=heuristic, weight=weight_attr
                )
            elif algorithm == "bellman_ford":
                path = nx.bellman_ford_path(
                    self.G, start_node, end_node, weight=weight_attr
                )
                cost = nx.bellman_ford_path_length(
                    self.G, start_node, end_node, weight=weight_attr
                )
            else:
                raise ValueError(f"Algoritmo '{algorithm}' no reconocido")

            stats = self._calculate_route_stats(path)

            print(f"\n✓ Ruta encontrada!")
            print(f"  - Nodos en la ruta: {len(path)}")
            print(f"  - Distancia total: {stats['total_distance']:.2f} metros")
            print(f"  - Riesgo promedio: {stats['avg_risk']:.4f}")
            print(f"  - Cámaras en ruta: {stats['total_cameras']}")
            print(f"  - Incidentes en ruta: {stats['total_incidents']}")
            print(f"  - Costo {optimization}: {cost:.4f}")

            return {
                "path": path,
                "cost": cost,
                "optimization": optimization,
                "algorithm": algorithm,
                "statistics": stats,
                "edges": self._get_edge_details(path),
            }

        except nx.NetworkXNoPath:
            print("✗ No se encontró ruta entre los puntos especificados")
            return None
        except Exception as e:
            print(f"✗ Error al calcular ruta: {str(e)}")
            return None

    def _calculate_route_stats(self, path: List[Tuple[float, float]]) -> Dict:
        total_distance = 0
        total_risk = 0
        total_cameras = 0
        total_incidents = 0
        edge_count = 0

        for i in range(len(path) - 1):
            edge_data = self.G[path[i]][path[i + 1]]
            total_distance += edge_data["length"]
            total_risk += edge_data["risk_score"]
            total_cameras += edge_data["cameras_count"]
            total_incidents += edge_data["incidents_count"]
            edge_count += 1

        return {
            "total_distance": total_distance,
            "avg_risk": total_risk / edge_count if edge_count > 0 else 0,
            "total_cameras": int(total_cameras),
            "total_incidents": int(total_incidents),
            "num_segments": edge_count,
        }

    def _get_edge_details(self, path: List[Tuple[float, float]]) -> List[Dict]:
        edges = []
        for i in range(len(path) - 1):
            edge_data = self.G[path[i]][path[i + 1]]
            edges.append(
                {
                    "from": path[i],
                    "to": path[i + 1],
                    "name": edge_data["name"],
                    "length": edge_data["length"],
                    "harassmentRisk": edge_data["harassmentRisk"],
                    "cameras_count": edge_data["cameras_count"],
                    "incidents_count": edge_data["incidents_count"],
                    "risk_score": edge_data["risk_score"],
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
