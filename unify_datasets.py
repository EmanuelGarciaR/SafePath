"""
Script para unificar los datasets de SafePath usando GeoPandas
Combina datos de calles, cámaras y incidentes de tránsito para calcular rutas óptimas
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely import wkt
import numpy as np

def load_streets_data(file_path):
    """
    Carga el dataset de calles con acoso y lo convierte a GeoDataFrame
    """
    print("Cargando datos de calles...")
    df = pd.read_csv(file_path, sep=';')
    
    # Convertir la columna geometry de texto a geometría
    df['geometry'] = df['geometry'].apply(wkt.loads)
    
    # Crear GeoDataFrame
    gdf_streets = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    print(f"Calles cargadas: {len(gdf_streets)} aristas")
    return gdf_streets

# print(load_streets_data('assets/calles_de_medellin_con_acoso.csv'))

def load_cameras_data(file_path):
    """
    Carga el dataset de cámaras y lo convierte a GeoDataFrame
    """
    print("Cargando datos de cámaras...")
    df = pd.read_csv(file_path)
    
    # Crear geometría Point desde latitud y longitud
    df['geometry'] = df.apply(lambda row: Point(row['longitud'], row['latitud']), axis=1)
    
    # Crear GeoDataFrame
    gdf_cameras = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    print(f"Cámaras cargadas: {len(gdf_cameras)} puntos")
    return gdf_cameras

# print(load_cameras_data('assets/camaras_ars__simm.csv'))

def load_incidents_data(file_path):
    """
    Carga el dataset de incidentes de tránsito y lo convierte a GeoDataFrame
    """
    print("Cargando datos de incidentes de tránsito...")
    df = pd.read_csv(file_path, encoding="latin1")
    
    # Filtrar filas sin coordenadas
    df = df.dropna(subset=['longitud', 'latitud'])
    
    # Crear geometría Point desde latitud y longitud
    df['geometry'] = df.apply(lambda row: Point(row['longitud'], row['latitud']), axis=1)
    
    # Crear GeoDataFrame
    gdf_incidents = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    print(f"Incidentes cargados: {len(gdf_incidents)} eventos")
    return gdf_incidents
#print(load_incidents_data(r"assets\total_incidentes_transito.csv"))



def calculate_cameras_per_edge(gdf_streets, gdf_cameras, buffer_distance=0.0005):
    """
    Calcula el promedio de cámaras cercanas a cada arista (calle)
    
    Args:
        gdf_streets: GeoDataFrame de calles
        gdf_cameras: GeoDataFrame de cámaras
        buffer_distance: Distancia de buffer en grados (~50m aprox)
    
    Returns:
        Serie con el número de cámaras por arista
    """
    print(f"Calculando densidad de cámaras por arista (buffer={buffer_distance*111000:.0f}m)...")
    
    cameras_count = []
    
    for idx, street in gdf_streets.iterrows():
        # Crear buffer alrededor de la arista
        buffered_line = street.geometry.buffer(buffer_distance)
        
        # Contar cuántas cámaras están dentro del buffer
        cameras_in_buffer = gdf_cameras[gdf_cameras.geometry.within(buffered_line)]
        cameras_count.append(len(cameras_in_buffer))
        
        if (idx + 1) % 10000 == 0:
            print(f"  Procesadas {idx + 1}/{len(gdf_streets)} aristas...")
    
    return pd.Series(cameras_count, index=gdf_streets.index)

def calculate_incidents_per_edge(gdf_streets, gdf_incidents, buffer_distance=0.0005):
    """
    Calcula el número de incidentes de tránsito cercanos a cada arista
    
    Args:
        gdf_streets: GeoDataFrame de calles
        gdf_incidents: GeoDataFrame de incidentes
        buffer_distance: Distancia de buffer en grados (~50m aprox)
    
    Returns:
        Serie con el número de incidentes por arista
    """
    print(f"Calculando densidad de incidentes por arista (buffer={buffer_distance*111000:.0f}m)...")
    
    incidents_count = []
    incidents_severity = []
    
    for idx, street in gdf_streets.iterrows():
        # Crear buffer alrededor de la arista
        buffered_line = street.geometry.buffer(buffer_distance)
        
        # Filtrar incidentes dentro del buffer
        incidents_in_buffer = gdf_incidents[gdf_incidents.geometry.within(buffered_line)]
        
        # Contar incidentes
        incidents_count.append(len(incidents_in_buffer))
        
        # Calcular gravedad (HERIDO=1, MUERTO=2, SOLO DAÑOS=0.5)
        severity_map = {'HERIDO': 1.0, 'MUERTO': 2.0, 'SOLO DAÑOS': 0.5, 'SOLO DA�OS': 0.5}
        if len(incidents_in_buffer) > 0:
            severity = incidents_in_buffer['gravedad'].map(severity_map).fillna(0.5).mean()
        else:
            severity = 0.0
        incidents_severity.append(severity)
        
        if (idx + 1) % 10000 == 0:
            print(f"  Procesadas {idx + 1}/{len(gdf_streets)} aristas...")
    
    return pd.Series(incidents_count, index=gdf_streets.index), pd.Series(incidents_severity, index=gdf_streets.index)

def normalize_column(series, method='minmax'):
    """
    Normaliza una serie de datos entre 0 y 1
    """
    if method == 'minmax':
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val == 0:
            return pd.Series(0, index=series.index)
        return (series - min_val) / (max_val - min_val)
    return series

def calculate_risk_score(gdf_streets):
    """
    Calcula un score de riesgo combinado basado en:
    - harassmentRisk (acoso)
    - Densidad de cámaras (más cámaras = menos riesgo)
    - Incidentes de tránsito (más incidentes = más riesgo)
    """
    print("Calculando score de riesgo combinado...")
    
    # Normalizar las métricas
    harassment_norm = normalize_column(gdf_streets['harassmentRisk'])
    
    # Para cámaras: invertir (más cámaras = menos riesgo)
    cameras_norm = normalize_column(gdf_streets['cameras_count'])
    cameras_safety = 1 - cameras_norm  # Invertir: más cámaras = más seguridad
    
    # Para incidentes: normalizar (más incidentes = más riesgo)
    incidents_norm = normalize_column(gdf_streets['incidents_count'])
    severity_norm = normalize_column(gdf_streets['incidents_severity'])
    
    # Combinar incidentes con gravedad
    traffic_risk = (incidents_norm * 0.7 + severity_norm * 0.3)
    
    # Score final de riesgo (pesos ajustables)
    # 40% acoso, 30% tráfico, 30% falta de cámaras
    risk_score = (
        harassment_norm * 0.4 + 
        traffic_risk * 0.3 + 
        cameras_safety * 0.3
    )
    
    return risk_score

def unify_datasets(streets_path, cameras_path, incidents_path, buffer_distance=0.0005):
    """
    Función principal que unifica los tres datasets
    
    Args:
        streets_path: Ruta al CSV de calles
        cameras_path: Ruta al CSV de cámaras
        incidents_path: Ruta al CSV de incidentes
        buffer_distance: Distancia de buffer para cálculos espaciales (en grados)
    
    Returns:
        GeoDataFrame unificado con todas las métricas
    """
    print("="*60)
    print("INICIANDO UNIFICACIÓN DE DATASETS - SAFEPATH")
    print("="*60)
    
    # 1. Cargar datos
    gdf_streets = load_streets_data(streets_path)
    gdf_cameras = load_cameras_data(cameras_path)
    gdf_incidents = load_incidents_data(incidents_path)
    
    print("\n" + "="*60)
    print("CALCULANDO MÉTRICAS ESPACIALES")
    print("="*60)
    
    # 2. Calcular cámaras por arista
    gdf_streets['cameras_count'] = calculate_cameras_per_edge(
        gdf_streets, gdf_cameras, buffer_distance
    )
    
    print()
    
    # 3. Calcular incidentes por arista
    gdf_streets['incidents_count'], gdf_streets['incidents_severity'] = calculate_incidents_per_edge(
        gdf_streets, gdf_incidents, buffer_distance
    )
    
    print()
    
    # 4. Calcular score de riesgo combinado
    gdf_streets['risk_score'] = calculate_risk_score(gdf_streets)
    
    # 5. Calcular costo combinado (distancia + riesgo)
    # Normalizar distancia
    distance_norm = normalize_column(gdf_streets['length'])
    
    # Peso ajustable: 50% distancia, 50% riesgo
    gdf_streets['combined_cost'] = (distance_norm * 0.5 + gdf_streets['risk_score'] * 0.5)
    
    print("\n" + "="*60)
    print("RESUMEN DE DATOS UNIFICADOS")
    print("="*60)
    print(f"Total de aristas: {len(gdf_streets)}")
    print(f"\nEstadísticas de cámaras:")
    print(f"  - Promedio por arista: {gdf_streets['cameras_count'].mean():.2f}")
    print(f"  - Máximo: {gdf_streets['cameras_count'].max()}")
    print(f"  - Aristas sin cámaras: {(gdf_streets['cameras_count'] == 0).sum()}")
    
    print(f"\nEstadísticas de incidentes:")
    print(f"  - Promedio por arista: {gdf_streets['incidents_count'].mean():.2f}")
    print(f"  - Máximo: {gdf_streets['incidents_count'].max()}")
    print(f"  - Aristas sin incidentes: {(gdf_streets['incidents_count'] == 0).sum()}")
    
    print(f"\nEstadísticas de riesgo:")
    print(f"  - Risk Score promedio: {gdf_streets['risk_score'].mean():.4f}")
    print(f"  - Risk Score máximo: {gdf_streets['risk_score'].max():.4f}")
    print(f"  - Risk Score mínimo: {gdf_streets['risk_score'].min():.4f}")
    
    print("\nColumnas en el dataset unificado:")
    print(gdf_streets.columns.tolist())
    
    return gdf_streets

def save_unified_data(gdf, output_path):
    """
    Guarda el GeoDataFrame unificado en diferentes formatos
    """
    print("\n" + "="*60)
    print("GUARDANDO DATOS UNIFICADOS")
    print("="*60)
    
    # Guardar como GeoJSON (compatible con Kepler.gl)
    geojson_path = output_path.replace('.csv', '.geojson')
    print(f"Guardando como GeoJSON: {geojson_path}")
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    # Guardar como CSV con geometría WKT
    csv_path = output_path
    print(f"Guardando como CSV: {csv_path}")
    gdf_copy = gdf.copy()
    gdf_copy['geometry'] = gdf_copy['geometry'].apply(lambda x: x.wkt)
    gdf_copy.to_csv(csv_path, index=False)
    
    print("✓ Datos guardados exitosamente!")
    return geojson_path, csv_path

if __name__ == "__main__":
    # Rutas de los archivos
    STREETS_PATH = "assets/calles_de_medellin_con_acoso.csv"
    CAMERAS_PATH = "assets/camaras_ars__simm.csv"
    INCIDENTS_PATH = "assets/total_incidentes_transito.csv"
    OUTPUT_PATH = "assets/unified_medellin_data.csv"
    
    # Distancia de buffer (0.0005 grados ≈ 55 metros)
    BUFFER_DISTANCE = 0.0005
    
    # Ejecutar unificación
    gdf_unified = unify_datasets(
        STREETS_PATH, 
        CAMERAS_PATH, 
        INCIDENTS_PATH,
        BUFFER_DISTANCE
    )
    
    # Guardar resultados
    geojson_file, csv_file = save_unified_data(gdf_unified, OUTPUT_PATH)
    
    print("\n" + "="*60)
    print("PROCESO COMPLETADO")
    print("="*60)
    print(f"Archivos generados:")
    print(f"  - CSV: {csv_file}")
    print(f"  - GeoJSON: {geojson_file}")
    print("\nLos archivos están listos para usarse en Kepler.gl")
    print("Para visualizar en Kepler.gl, carga el archivo .geojson")
