"""
SafePath - Algoritmos Avanzados de Ruteo (Backend)
"""
from typing import Tuple, List, Dict
import heapq

import networkx as nx
import numpy as np

from .route_optimizer import SafePathRouter


class AdvancedRouter(SafePathRouter):
    def __init__(self, unified_data_path: str | None = None):
        super().__init__(unified_data_path)
        print(
            "Algoritmos avanzados disponibles: greedy, backtracking, branch_and_bound, k_shortest"
        )

    def greedy_route(
        self, origin: Tuple[float, float], destination: Tuple[float, float], optimization: str = "combined"
    ) -> Dict:
        print(f"\n{'=' * 60}")
        print(f"ALGORITMO GREEDY - Optimización: {optimization}")
        print(f"{'=' * 60}")

        start_node = self.find_nearest_node(origin[0], origin[1])
        end_node = self.find_nearest_node(destination[0], destination[1])
        weight_attr = f"weight_{optimization}"

        path = [start_node]
        current = start_node
        visited = {start_node}
        total_cost = 0

        max_iterations = 10000
        iterations = 0

        while current != end_node and iterations < max_iterations:
            neighbors = [
                (n, self.G[current][n][weight_attr]) for n in self.G.neighbors(current) if n not in visited
            ]
            if not neighbors:
                print("✗ Greedy: No hay vecinos disponibles, sin ruta")
                return None
            next_node = min(neighbors, key=lambda x: x[1])[0]
            edge_cost = self.G[current][next_node][weight_attr]
            path.append(next_node)
            visited.add(next_node)
            total_cost += edge_cost
            current = next_node
            iterations += 1

        if current != end_node:
            print("✗ Greedy: No se alcanzó el destino")
            return None

        stats = self._calculate_route_stats(path)
        print("✓ Ruta Greedy encontrada!")
        print(f"  - Nodos: {len(path)}")
        print(f"  - Iteraciones: {iterations}")
        print(f"  - Distancia: {stats['total_distance']:.2f} m")
        print(f"  - Costo {optimization}: {total_cost:.4f}")

        return {
            "path": path,
            "cost": total_cost,
            "optimization": optimization,
            "algorithm": "greedy",
            "statistics": stats,
            "edges": self._get_edge_details(path),
        }

    def backtracking_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        optimization: str = "combined",
        max_cost: float = float("inf"),
    ) -> Dict:
        print(f"\n{'=' * 60}")
        print(f"ALGORITMO BACKTRACKING - Optimización: {optimization}")
        print(f"{'=' * 60}")

        start_node = self.find_nearest_node(origin[0], origin[1])
        end_node = self.find_nearest_node(destination[0], destination[1])
        weight_attr = f"weight_{optimization}"

        best_path = None
        best_cost = float("inf")
        nodes_explored = [0]

        def backtrack(current: Tuple, path: List, cost: float, visited: set):
            nonlocal best_path, best_cost
            nodes_explored[0] += 1
            if current == end_node:
                if cost < best_cost:
                    best_cost = cost
                    best_path = path.copy()
                return
            if cost >= best_cost or cost > max_cost:
                return
            if len(path) > 100:
                return
            for neighbor in self.G.neighbors(current):
                if neighbor not in visited:
                    edge_cost = self.G[current][neighbor][weight_attr]
                    new_cost = cost + edge_cost
                    if new_cost < best_cost and new_cost <= max_cost:
                        visited.add(neighbor)
                        path.append(neighbor)
                        backtrack(neighbor, path, new_cost, visited)
                        path.pop()
                        visited.remove(neighbor)

        initial_visited = {start_node}
        backtrack(start_node, [start_node], 0, initial_visited)

        if best_path is None:
            print("✗ Backtracking: No se encontró ruta")
            return None

        stats = self._calculate_route_stats(best_path)
        print("✓ Ruta Backtracking encontrada!")
        print(f"  - Nodos explorados: {nodes_explored[0]}")
        print(f"  - Nodos en ruta: {len(best_path)}")
        print(f"  - Distancia: {stats['total_distance']:.2f} m")
        print(f"  - Costo {optimization}: {best_cost:.4f}")

        return {
            "path": best_path,
            "cost": best_cost,
            "optimization": optimization,
            "algorithm": "backtracking",
            "statistics": stats,
            "edges": self._get_edge_details(best_path),
            "nodes_explored": nodes_explored[0],
        }

    def branch_and_bound_route(
        self, origin: Tuple[float, float], destination: Tuple[float, float], optimization: str = "combined"
    ) -> Dict:
        print(f"\n{'=' * 60}")
        print(f"BRANCH AND BOUND - Optimización: {optimization}")
        print(f"{'=' * 60}")

        start_node = self.find_nearest_node(origin[0], origin[1])
        end_node = self.find_nearest_node(destination[0], destination[1])
        weight_attr = f"weight_{optimization}"

        pq = [(0, start_node, [start_node])]
        best_cost = float("inf")
        best_path = None
        visited_with_cost = {}
        nodes_explored = 0

        while pq:
            current_cost, current_node, path = heapq.heappop(pq)
            nodes_explored += 1
            if current_node == end_node:
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_path = path
                continue
            if current_node in visited_with_cost and visited_with_cost[current_node] <= current_cost:
                continue
            visited_with_cost[current_node] = current_cost
            if current_cost >= best_cost:
                continue
            if len(path) > 100:
                continue
            for neighbor in self.G.neighbors(current_node):
                if neighbor not in path:
                    edge_cost = self.G[current_node][neighbor][weight_attr]
                    new_cost = current_cost + edge_cost
                    if new_cost < best_cost:
                        new_path = path + [neighbor]
                        heapq.heappush(pq, (new_cost, neighbor, new_path))

        if best_path is None:
            print("✗ Branch and Bound: No se encontró ruta")
            return None

        stats = self._calculate_route_stats(best_path)
        print("✓ Ruta Branch and Bound encontrada!")
        print(f"  - Nodos explorados: {nodes_explored}")
        print(f"  - Nodos en ruta: {len(best_path)}")
        print(f"  - Distancia: {stats['total_distance']:.2f} m")
        print(f"  - Costo {optimization}: {best_cost:.4f}")

        return {
            "path": best_path,
            "cost": best_cost,
            "optimization": optimization,
            "algorithm": "branch_and_bound",
            "statistics": stats,
            "edges": self._get_edge_details(best_path),
            "nodes_explored": nodes_explored,
        }

    def k_shortest_paths(
        self, origin: Tuple[float, float], destination: Tuple[float, float], k: int = 3, optimization: str = "combined"
    ) -> List[Dict]:
        print(f"\n{'=' * 60}")
        print(f"K-SHORTEST PATHS (k={k}) - Optimización: {optimization}")
        print(f"{'=' * 60}")

        start_node = self.find_nearest_node(origin[0], origin[1])
        end_node = self.find_nearest_node(destination[0], destination[1])
        weight_attr = f"weight_{optimization}"

        try:
            paths_generator = nx.shortest_simple_paths(self.G, start_node, end_node, weight=weight_attr)
            routes = []
            for i, path in enumerate(paths_generator):
                if i >= k:
                    break
                cost = sum(self.G[path[j]][path[j + 1]][weight_attr] for j in range(len(path) - 1))
                stats = self._calculate_route_stats(path)
                routes.append(
                    {
                        "path": path,
                        "cost": cost,
                        "rank": i + 1,
                        "optimization": optimization,
                        "algorithm": "k_shortest_paths",
                        "statistics": stats,
                        "edges": self._get_edge_details(path),
                    }
                )
                print(f"\n  Ruta #{i + 1}:")
                print(f"    - Distancia: {stats['total_distance']:.2f} m")
                print(f"    - Riesgo promedio: {stats['avg_risk']:.4f}")
                print(f"    - Costo: {cost:.4f}")
            print(f"\n✓ Se encontraron {len(routes)} rutas alternativas")
            return routes
        except nx.NetworkXNoPath:
            print("✗ No se encontraron rutas")
            return []
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return []

    def compare_all_algorithms(
        self, origin: Tuple[float, float], destination: Tuple[float, float], optimization: str = "combined"
    ) -> Dict:
        print("\n" + "=" * 70)
        print("COMPARACIÓN DE TODOS LOS ALGORITMOS")
        print("=" * 70)

        results = {}
        print("\n[1/6] Dijkstra (óptimo garantizado)...")
        results["dijkstra"] = self.calculate_route(origin, destination, optimization, "dijkstra")
        print("\n[2/6] A* (búsqueda heurística)...")
        results["astar"] = self.calculate_route(origin, destination, optimization, "astar")
        print("\n[3/6] Greedy (voraz)...")
        results["greedy"] = self.greedy_route(origin, destination, optimization)
        print("\n[4/6] Branch and Bound...")
        results["branch_and_bound"] = self.branch_and_bound_route(origin, destination, optimization)
        print("\n[5/6] K-Shortest Paths (3 alternativas)...")
        k_routes = self.k_shortest_paths(origin, destination, k=3, optimization=optimization)
        results["k_shortest"] = k_routes

        print("\n" + "=" * 70)
        print("RESUMEN COMPARATIVO")
        print("=" * 70)
        print(f"{'Algoritmo':<20} {'Distancia (m)':<15} {'Riesgo':<10} {'Costo':<10}")
        print("-" * 70)
        for name, route in results.items():
            if route and name != "k_shortest":
                stats = route["statistics"]
                print(
                    f"{name:<20} {stats['total_distance']:<15.2f} {stats['avg_risk']:<10.4f} {route['cost']:<10.4f}"
                )
        return results


if __name__ == "__main__":
    from pathlib import Path

    print("\n" + "=" * 70)
    print("DEMO: ALGORITMOS AVANZADOS DE RUTEO")
    print("=" * 70)

    router = AdvancedRouter()
    origin = (-75.5657, 6.2080)
    destination = (-75.5676, 6.2528)

    comparison = router.compare_all_algorithms(origin, destination, "combined")

    repo_root = Path(__file__).resolve().parents[1]
    for algo_name, route in comparison.items():
        if route and algo_name != "k_shortest":
            output_file = repo_root / f"assets/route_{algo_name}.geojson"
            router.export_route_to_geojson(route, str(output_file))

    print("\n" + "=" * 70)
    print("DEMO COMPLETADA - Revisa los archivos .geojson generados")
    print("=" * 70)
