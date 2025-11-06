# SafePath

Sistema de optimización y visualización de rutas seguras en Medellín, que combina datos de acoso callejero, cámaras de seguridad e incidentes de tránsito para calcular rutas equilibrando distancia y riesgo.

---

## Descripción del Proyecto

SafePath es una aplicación web completa que permite a los usuarios calcular rutas óptimas en Medellín considerando múltiples factores de seguridad urbana. El sistema integra tres fuentes de datos geoespaciales, aplica algoritmos de grafos para el cálculo de rutas, y ofrece una interfaz de visualización interactiva para explorar las opciones disponibles.

### Objetivo
Proporcionar rutas alternativas que permitan a los usuarios elegir entre:
- Rutas más cortas (menor distancia física)
- Rutas más seguras (menor riesgo de acoso e incidentes)
- Rutas con menos incidentes de tránsito
- Rutas balanceadas (combinación óptima de distancia y seguridad)

---

## Estructura del Proyecto

```
SafePath/
├── backend/              # Backend Python con FastAPI
│   ├── api.py           # Servidor REST con endpoint /route
│   ├── route_optimizer.py     # Motor de ruteo con NetworkX
│   ├── advanced_routing.py    # Algoritmos de búsqueda avanzados
│   └── unify_datasets.py      # Pipeline de unificación de datos
├── front/               # Frontend React + Kepler.gl (requiere Node.js)
│   ├── src/
│   │   ├── App.jsx     # Interfaz de usuario y llamadas a API
│   │   ├── main.jsx    # Punto de entrada y configuración Redux
│   │   └── store.js    # Store Redux para Kepler.gl
│   ├── package.json
│   └── vite.config.js
├── front-static/        # Alternativa sin Node.js (HTML + Mapbox GL CDN)
│   └── index.html      # UI básica para visualización rápida
├── assets/              # Datasets y archivos generados
│   ├── calles_de_medellin_con_acoso.csv
│   ├── camaras_ars__simm.csv
│   ├── total_incidentes_transito.csv
│   ├── unified_medellin_data.csv      # Dataset procesado
│   └── unified_medellin_data.geojson  # Exportación GeoJSON
├── requirements.txt     # Dependencias Python
└── README.md           # Este archivo
```

---

## Componentes Principales

### 1. Pipeline de Unificación de Datos (`backend/unify_datasets.py`)

**Función:** Integrar y procesar tres fuentes de datos geoespaciales en un único dataset normalizado.

**Datasets de entrada:**
- `calles_de_medellin_con_acoso.csv`: Calles con índice de riesgo de acoso (harassmentRisk)
- `camaras_ars__simm.csv`: Ubicación de cámaras de seguridad
- `total_incidentes_transito.csv`: Incidentes de tránsito con gravedad

**Proceso:**
1. Carga de datos usando GeoPandas con geometrías LineString/Point
2. Cálculo espacial de métricas por arista:
   - `cameras_count`: Número de cámaras en un buffer de ~55m alrededor de cada calle
   - `incidents_count`: Cantidad de incidentes cercanos
   - `incidents_severity`: Gravedad promedio de incidentes (0-2)
3. Normalización min-max de todas las métricas a escala 0-1
4. Cálculo de `risk_score` combinado:
   ```
   risk_score = 0.4 × harassmentRisk_norm 
              + 0.3 × traffic_risk
              + 0.3 × (1 - cameras_norm)
   
   donde traffic_risk = 0.7 × incidents_norm + 0.3 × severity_norm
   ```
5. Cálculo de `combined_cost` balanceado:
   ```
   combined_cost = 0.5 × distance_norm + 0.5 × risk_score
   ```

**Salida:**
- CSV y GeoJSON con columnas: name, origin, destination, length, oneway, harassmentRisk, cameras_count, incidents_count, incidents_severity, risk_score, combined_cost, geometry

### 2. Motor de Ruteo (`backend/route_optimizer.py`)

**Función:** Construir grafo dirigido y calcular rutas óptimas con múltiples criterios.

**Implementación:**
- **Clase:** `SafePathRouter`
- **Grafo:** NetworkX DiGraph
  - Nodos: Intersecciones (coordenadas lon/lat únicas)
  - Aristas: Calles con atributos de peso múltiple
- **Pesos disponibles:**
  - `weight_distance`: Longitud física en metros
  - `weight_risk`: Score de riesgo (0-1)
  - `weight_combined`: Balance 50-50 distancia/riesgo
  - `weight_incidents`: Métrica basada en incidentes de tránsito

**Algoritmos clásicos implementados:**
- **Dijkstra**: Algoritmo estándar, garantiza óptimo (recomendado para producción)
- **A\***: Optimización con heurística de distancia euclidiana, más rápido que Dijkstra
- **Bellman-Ford**: Soporta pesos negativos, más lento pero robusto

**Funcionalidad:**
- Búsqueda de nodo más cercano a coordenadas dadas
- Cálculo de ruta con optimización configurable
- Estadísticas de ruta: distancia total, riesgo promedio, cámaras, incidentes
- Exportación de rutas a GeoJSON para visualización

### 3. Algoritmos Avanzados (`backend/advanced_routing.py`)

**Función:** Extensión de `SafePathRouter` con estrategias de búsqueda alternativas.

**Clase:** `AdvancedRouter` (hereda de SafePathRouter)

**Algoritmos adicionales:**
- **Greedy (voraz):** Selección del vecino con menor costo inmediato; rápido pero no garantiza óptimo
- **Backtracking:** Exploración exhaustiva con retroceso; garantiza óptimo en grafos pequeños
- **Branch and Bound:** Exploración con poda inteligente mediante cola de prioridad
- **K-Shortest Paths:** Algoritmo de Yen para obtener k mejores rutas alternativas

**Utilidad:**
- Comparación de diferentes enfoques algorítmicos
- Generación de opciones múltiples para el usuario
- Análisis de trade-offs entre tiempo de cómputo y calidad de solución

### 4. API Backend (`backend/api.py`)

**Función:** Servidor REST que expone la funcionalidad de ruteo.

**Framework:** FastAPI con CORS habilitado

**Endpoints:**
- `GET /health`: Verificación de disponibilidad del servicio
- `GET /route`: Cálculo de ruta con parámetros:
  - `origin_lon`, `origin_lat`: Coordenadas de origen
  - `dest_lon`, `dest_lat`: Coordenadas de destino
  - `optimization`: Tipo de optimización (distance, risk, incidents, combined)
  - `algorithm`: Algoritmo a usar (dijkstra, astar, bellman_ford)

**Respuesta:** GeoJSON FeatureCollection con:
- Geometrías LineString de cada segmento de la ruta
- Properties con atributos de cada calle
- Metadatos: estadísticas agregadas, costo total, parámetros usados

**Configuración:**
- Puerto por defecto: 8000
- Recarga automática en desarrollo
- CORS para localhost:5173 y localhost:3000

### 5. Frontend React + Kepler.gl (`front/`)

**Función:** Interfaz web interactiva para visualización de rutas.

**Stack tecnológico:**
- React 18.2.0
- Kepler.gl 3.0.0 (visualización geoespacial avanzada)
- Mapbox GL 2.15.0 (mapa base)
- Redux + React Redux (estado global)
- Vite 5.x (bundler y servidor de desarrollo)

**Características:**
- Formulario de entrada para origen/destino (lon, lat)
- Selectores para optimización y algoritmo
- Integración con Kepler.gl para renderizado de capas GeoJSON
- Visualización de múltiples rutas simultáneas
- Centralización automática del mapa en la ruta calculada

**Configuración:**
- Variables de entorno en `.env.local`:
  - `VITE_MAPBOX_TOKEN`: Token de acceso de Mapbox (obligatorio)
  - `VITE_API_BASE`: URL del backend (default: http://localhost:8000)

### 6. Frontend Estático (`front-static/`)

**Función:** Alternativa sin dependencias de Node.js para visualización básica.

**Implementación:**
- HTML + JavaScript vanilla
- Mapbox GL JS vía CDN
- Fetch API para llamadas al backend
- Sin bundler ni npm requerido

**Uso:** Solución de respaldo cuando hay problemas con npm o para demos rápidas.

---

## Proceso de Desarrollo

### Fase 1: Unificación de Datos
- Carga de datasets CSV con GeoPandas
- Manejo de encodings (latin1 para incidentes)
- Resolución de problemas con paths de Windows (barras invertidas)
- Implementación de buffers espaciales para cálculo de métricas por arista
- Normalización de todas las variables a escala común
- Diseño de fórmulas de riesgo ponderadas
- Decisión de NO almacenar promedio global de cámaras, usar métricas por arista

### Fase 2: Motor de Ruteo
- Construcción de grafo dirigido con NetworkX
- Implementación de múltiples pesos por arista
- Desarrollo de algoritmos clásicos (Dijkstra, A*, Bellman-Ford)
- Adición de peso `weight_incidents` para optimización específica
- Implementación de heurística geográfica para A*
- Sistema de cálculo de estadísticas de ruta
- Exportación a GeoJSON compatible con Kepler.gl

### Fase 3: Algoritmos Avanzados
- Extensión del router base con herencia
- Implementación de estrategias alternativas de búsqueda
- Algoritmo K-Shortest Paths para generación de alternativas
- Sistema de comparación entre algoritmos
- Documentación técnica en ROUTING_GUIDE.md

### Fase 4: API REST
- Diseño de endpoint RESTful con FastAPI
- Implementación de parámetros de consulta
- Configuración de CORS para desarrollo local
- Integración con router de NetworkX
- Manejo de errores y respuestas vacías
- Transformación de geometrías WKT a GeoJSON

### Fase 5: Frontend
- Scaffolding de aplicación React con Vite
- Integración de Kepler.gl con Redux
- Resolución de conflictos de dependencias (styled-components, React versions)
- Importación de CSS requerido (Mapbox GL, Kepler.gl)
- Diseño de interfaz con controles de entrada
- Implementación de llamadas fetch al backend
- Sistema de capas dinámicas en Kepler.gl

### Fase 6: Reorganización del Proyecto
- Separación de código backend en carpeta `backend/`
- Migración de frontend a carpeta `front/`
- Ajuste de imports y referencias de módulos
- Actualización de documentación (README, ROUTING_GUIDE)
- Creación de frontend estático como alternativa sin Node

### Fase 7: Ajustes Finales
- Manejo de problemas de npm registry (json.schemastore)
- Creación de solución alternativa sin node_modules
- Documentación de proceso de obtención de Mapbox token
- Limpieza de archivos duplicados pendiente

---

## Tecnologías y Librerías

### Backend (Python 3.10+)
- **pandas**: Manipulación de datos tabulares
- **geopandas**: Operaciones espaciales sobre geometrías
- **shapely**: Geometrías y operaciones geométricas
- **networkx**: Construcción y análisis de grafos
- **numpy**: Operaciones numéricas y normalización
- **fastapi**: Framework web asíncrono
- **uvicorn**: Servidor ASGI para FastAPI
- **pydantic**: Validación de datos

### Frontend (Node.js 18+)
- **React 18**: Librería de UI
- **Kepler.gl 3.0**: Plataforma de visualización geoespacial
- **Mapbox GL 2.15**: Mapas interactivos
- **Redux**: Gestión de estado
- **React Redux**: Bindings de Redux para React
- **styled-components 5.3**: CSS-in-JS
- **Vite 5**: Build tool y dev server

---

## Algoritmos de Ruteo: Resumen Técnico

### Métricas de Evaluación
| Algoritmo | Velocidad | Optimalidad | Memoria | Caso de Uso |
|-----------|-----------|-------------|---------|-------------|
| Dijkstra | Alta | Garantizada | Media | Producción general |
| A* | Muy Alta | Garantizada | Media | Respuestas rápidas |
| Bellman-Ford | Baja | Garantizada | Media | Pesos negativos |
| Greedy | Muy Alta | No garantizada | Muy baja | Aproximaciones |
| Branch & Bound | Media | Garantizada | Media | Balance óptimo/velocidad |
| Backtracking | Muy Baja | Garantizada | Baja | Grafos pequeños |
| K-Shortest Paths | Baja | Top-K garantizado | Alta | Múltiples alternativas |

### Fórmulas de Costo

**Risk Score:**
```
risk_score = 0.4 × harassmentRisk_norm 
           + 0.3 × (0.7 × incidents_norm + 0.3 × severity_norm)
           + 0.3 × (1 - cameras_norm)
```

**Combined Cost:**
```
combined_cost = 0.5 × distance_norm + 0.5 × risk_score
```

**Heurística A* (distancia euclidiana en metros):**
```
h(n1, n2) = sqrt((lon1-lon2)² + (lat1-lat2)²) × 111000
```

---

## Datasets

### Entrada
- **calles_de_medellin_con_acoso.csv**: ~50k calles con geometría LineString y harassmentRisk
- **camaras_ars__simm.csv**: ~1.2k cámaras con coordenadas Point
- **total_incidentes_transito.csv**: ~15k incidentes con coordenadas y gravedad

### Salida
- **unified_medellin_data.csv**: Dataset consolidado con 13 columnas
- **unified_medellin_data.geojson**: Versión GeoJSON para visualización directa

---

## Configuración y Ejecución

### Backend
```powershell
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python -m uvicorn backend.api:app --reload --port 8000
```

### Frontend (React)
```powershell
cd front
Copy-Item .env.example .env.local
# Editar .env.local con VITE_MAPBOX_TOKEN
npm install
npm run dev
```

### Frontend (Estático)
```powershell
# Crear env.local.js en front-static/ con token
python -m http.server 5500
# Abrir http://localhost:5500/front-static/
```

---

## Estado Actual y Próximos Pasos

### Completado
- ✅ Unificación de datasets con métricas espaciales
- ✅ Motor de ruteo con múltiples algoritmos
- ✅ API REST funcional
- ✅ Frontend React con Kepler.gl
- ✅ Frontend estático alternativo
- ✅ Documentación técnica

### Pendiente
- ⏳ Limpieza de archivos duplicados en raíz
- ⏳ Remoción de carpeta `web/` obsoleta
- ⏳ Optimización de performance con índices espaciales
- ⏳ Tests unitarios para backend
- ⏳ Deployment en producción

---

## Licencia
Ver archivo LICENSE en el repositorio.

---

## Autor
Emanuel García R. - 2025
