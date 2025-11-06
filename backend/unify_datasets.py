"""
Script para unificar los datasets de SafePath usando GeoPandas (Backend)
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import Point


def load_streets_data(file_path):
    print("Cargando datos de calles...")
    df = pd.read_csv(file_path, sep=";")
    df["geometry"] = df["geometry"].apply(wkt.loads)
    gdf_streets = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    print(f"Calles cargadas: {len(gdf_streets)} aristas")
    return gdf_streets


def load_cameras_data(file_path):
    print("Cargando datos de cámaras...")
    df = pd.read_csv(file_path)
    df["geometry"] = df.apply(lambda r: Point(r["longitud"], r["latitud"]), axis=1)
    gdf_cameras = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    print(f"Cámaras cargadas: {len(gdf_cameras)} puntos")
    return gdf_cameras


def load_incidents_data(file_path):
    print("Cargando datos de incidentes de tránsito...")
    df = pd.read_csv(file_path, encoding="latin1")
    df = df.dropna(subset=["longitud", "latitud"])
    df["geometry"] = df.apply(lambda r: Point(r["longitud"], r["latitud"]), axis=1)
    gdf_incidents = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    print(f"Incidentes cargados: {len(gdf_incidents)} eventos")
    return gdf_incidents


def calculate_cameras_per_edge(gdf_streets, gdf_cameras, buffer_distance=0.0005):
    print(
        f"Calculando densidad de cámaras por arista (buffer={buffer_distance*111000:.0f}m)..."
    )
    cameras_count = []
    for idx, street in gdf_streets.iterrows():
        buffered = street.geometry.buffer(buffer_distance)
        cameras_in_buffer = gdf_cameras[gdf_cameras.geometry.within(buffered)]
        cameras_count.append(len(cameras_in_buffer))
        if (idx + 1) % 10000 == 0:
            print(f"  Procesadas {idx + 1}/{len(gdf_streets)} aristas...")
    return pd.Series(cameras_count, index=gdf_streets.index)


def calculate_incidents_per_edge(gdf_streets, gdf_incidents, buffer_distance=0.0005):
    print(
        f"Calculando densidad de incidentes por arista (buffer={buffer_distance*111000:.0f}m)..."
    )
    incidents_count = []
    incidents_severity = []
    severity_map = {"HERIDO": 1.0, "MUERTO": 2.0, "SOLO DAÑOS": 0.5, "SOLO DA�OS": 0.5}

    for idx, street in gdf_streets.iterrows():
        buffered = street.geometry.buffer(buffer_distance)
        inc_buf = gdf_incidents[gdf_incidents.geometry.within(buffered)]
        incidents_count.append(len(inc_buf))
        if len(inc_buf) > 0:
            severity = inc_buf["gravedad"].map(severity_map).fillna(0.5).mean()
        else:
            severity = 0.0
        incidents_severity.append(severity)
        if (idx + 1) % 10000 == 0:
            print(f"  Procesadas {idx + 1}/{len(gdf_streets)} aristas...")
    return (
        pd.Series(incidents_count, index=gdf_streets.index),
        pd.Series(incidents_severity, index=gdf_streets.index),
    )


def normalize_column(series, method="minmax"):
    if method == "minmax":
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val == 0:
            return pd.Series(0, index=series.index)
        return (series - min_val) / (max_val - min_val)
    return series


def calculate_risk_score(gdf_streets):
    print("Calculando score de riesgo combinado...")
    harassment_norm = normalize_column(gdf_streets["harassmentRisk"])  
    cameras_norm = normalize_column(gdf_streets["cameras_count"])   
    cameras_safety = 1 - cameras_norm
    incidents_norm = normalize_column(gdf_streets["incidents_count"])
    severity_norm = normalize_column(gdf_streets["incidents_severity"])
    traffic_risk = incidents_norm * 0.7 + severity_norm * 0.3
    risk_score = harassment_norm * 0.4 + traffic_risk * 0.3 + cameras_safety * 0.3
    return risk_score


def unify_datasets(streets_path, cameras_path, incidents_path, buffer_distance=0.0005):
    print("=" * 60)
    print("INICIANDO UNIFICACIÓN DE DATASETS - SAFEPATH")
    print("=" * 60)

    gdf_streets = load_streets_data(streets_path)
    gdf_cameras = load_cameras_data(cameras_path)
    gdf_incidents = load_incidents_data(incidents_path)

    print("\n" + "=" * 60)
    print("CALCULANDO MÉTRICAS ESPACIALES")
    print("=" * 60)

    gdf_streets["cameras_count"] = calculate_cameras_per_edge(
        gdf_streets, gdf_cameras, buffer_distance
    )

    print()

    gdf_streets["incidents_count"], gdf_streets["incidents_severity"] = calculate_incidents_per_edge(
        gdf_streets, gdf_incidents, buffer_distance
    )

    print()

    gdf_streets["risk_score"] = calculate_risk_score(gdf_streets)

    distance_norm = normalize_column(gdf_streets["length"])  
    gdf_streets["combined_cost"] = distance_norm * 0.5 + gdf_streets["risk_score"] * 0.5

    print("\n" + "=" * 60)
    print("RESUMEN DE DATOS UNIFICADOS")
    print("=" * 60)
    print(f"Total de aristas: {len(gdf_streets)}")

    print("\nColumnas en el dataset unificado:")
    print(gdf_streets.columns.tolist())

    return gdf_streets


def save_unified_data(gdf, output_path):
    print("\n" + "=" * 60)
    print("GUARDANDO DATOS UNIFICADOS")
    print("=" * 60)

    geojson_path = output_path.replace(".csv", ".geojson")
    print(f"Guardando como GeoJSON: {geojson_path}")
    gdf.to_file(geojson_path, driver="GeoJSON")

    csv_path = output_path
    print(f"Guardando como CSV: {csv_path}")
    gdf_copy = gdf.copy()
    gdf_copy["geometry"] = gdf_copy["geometry"].apply(lambda x: x.wkt)
    gdf_copy.to_csv(csv_path, index=False)

    print("✓ Datos guardados exitosamente!")
    return geojson_path, csv_path


if __name__ == "__main__":
    # Resolver rutas respecto al repo root
    repo_root = Path(__file__).resolve().parents[1]
    assets = repo_root / "assets"

    STREETS_PATH = str(assets / "calles_de_medellin_con_acoso.csv")
    CAMERAS_PATH = str(assets / "camaras_ars__simm.csv")
    INCIDENTS_PATH = str(assets / "total_incidentes_transito.csv")
    OUTPUT_PATH = str(assets / "unified_medellin_data.csv")

    BUFFER_DISTANCE = 0.0005

    gdf_unified = unify_datasets(
        STREETS_PATH, CAMERAS_PATH, INCIDENTS_PATH, BUFFER_DISTANCE
    )

    geojson_file, csv_file = save_unified_data(gdf_unified, OUTPUT_PATH)

    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    print(f"Archivos generados:")
    print(f"  - CSV: {csv_file}")
    print(f"  - GeoJSON: {geojson_file}")
    print("\nLos archivos están listos para usarse en Kepler.gl")
