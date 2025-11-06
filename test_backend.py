"""
Script de prueba para verificar el backend de SafePath
"""
import requests
import json

API_BASE = "http://localhost:8000"

def test_health():
    """Prueba el endpoint de salud"""
    print("\n=== Test 1: Health Check ===")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_route():
    """Prueba el endpoint de cálculo de ruta"""
    print("\n=== Test 2: Route Calculation ===")
    
    params = {
        "origin_lon": -75.5657,
        "origin_lat": 6.2080,
        "dest_lon": -75.5676,
        "dest_lat": 6.2528,
        "optimization": "combined",
        "algorithm": "dijkstra"
    }
    
    print(f"Parámetros: {params}")
    
    try:
        response = requests.get(f"{API_BASE}/route", params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tipo: {data.get('type')}")
            print(f"Features: {len(data.get('features', []))}")
            
            if 'properties' in data:
                stats = data['properties'].get('statistics', {})
                print(f"\nEstadísticas:")
                print(f"  - Distancia total: {stats.get('total_distance', 0):.2f} m")
                print(f"  - Riesgo promedio: {stats.get('avg_risk', 0):.4f}")
                print(f"  - Cámaras: {stats.get('total_cameras', 0)}")
                print(f"  - Incidentes: {stats.get('total_incidents', 0)}")
                print(f"  - Segmentos: {stats.get('num_segments', 0)}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_all_algorithms():
    """Prueba todos los algoritmos disponibles"""
    print("\n=== Test 3: Comparación de Algoritmos ===")
    
    algorithms = ["dijkstra", "astar", "bellman_ford"]
    results = {}
    
    params = {
        "origin_lon": -75.5657,
        "origin_lat": 6.2080,
        "dest_lon": -75.5676,
        "dest_lat": 6.2528,
        "optimization": "combined"
    }
    
    for algo in algorithms:
        params["algorithm"] = algo
        print(f"\nProbando {algo}...")
        
        try:
            response = requests.get(f"{API_BASE}/route", params=params)
            if response.status_code == 200:
                data = response.json()
                stats = data.get('properties', {}).get('statistics', {})
                results[algo] = {
                    "distance": stats.get('total_distance', 0),
                    "risk": stats.get('avg_risk', 0),
                    "segments": stats.get('num_segments', 0)
                }
                print(f"  ✓ Distancia: {results[algo]['distance']:.2f} m")
            else:
                print(f"  ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return results

def test_optimizations():
    """Prueba todos los tipos de optimización"""
    print("\n=== Test 4: Tipos de Optimización ===")
    
    optimizations = ["distance", "risk", "incidents", "combined"]
    results = {}
    
    params = {
        "origin_lon": -75.5657,
        "origin_lat": 6.2080,
        "dest_lon": -75.5676,
        "dest_lat": 6.2528,
        "algorithm": "dijkstra"
    }
    
    for opt in optimizations:
        params["optimization"] = opt
        print(f"\nProbando optimización: {opt}...")
        
        try:
            response = requests.get(f"{API_BASE}/route", params=params)
            if response.status_code == 200:
                data = response.json()
                stats = data.get('properties', {}).get('statistics', {})
                results[opt] = {
                    "distance": stats.get('total_distance', 0),
                    "risk": stats.get('avg_risk', 0),
                    "cost": data.get('properties', {}).get('cost', 0)
                }
                print(f"  ✓ Distancia: {results[opt]['distance']:.2f} m")
                print(f"  ✓ Riesgo: {results[opt]['risk']:.4f}")
                print(f"  ✓ Costo: {results[opt]['cost']:.4f}")
            else:
                print(f"  ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return results

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBAS DEL BACKEND SAFEPATH")
    print("=" * 60)
    print("\nAsegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("Ejecuta: python -m uvicorn backend.api:app --reload --port 8000")
    
    input("\nPresiona Enter para continuar...")
    
    # Ejecutar pruebas
    success = True
    
    success = test_health() and success
    success = test_route() and success
    test_all_algorithms()
    test_optimizations()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TODAS LAS PRUEBAS BÁSICAS PASARON")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
    print("=" * 60)
