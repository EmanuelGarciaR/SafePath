# SafePath Frontend - Estructura Refactorizada

## 📁 Estructura de Archivos

```
src/
├── components/          # Componentes reutilizables
│   ├── Map.jsx         # Mapa MapLibre con marcadores y rutas
│   ├── SearchInput.jsx # Input de búsqueda con autocompletado
│   ├── RouteControls.jsx # Controles de algoritmo y optimización
│   ├── RouteStats.jsx  # Estadísticas de ruta única
│   ├── ComparisonPanel.jsx # Panel de comparación de rutas
│   └── index.js        # Exportaciones centralizadas
├── hooks/              # Custom React Hooks
│   ├── useGeocoding.js # Lógica de búsqueda de lugares
│   ├── useRouting.js   # Lógica de cálculo de rutas
│   └── index.js        # Exportaciones centralizadas
├── App.jsx             # Componente principal (orquestador)
├── App.css             # Estilos globales
├── main.jsx            # Entry point
└── index.css           # Estilos base
```

## 🧩 Componentes

### `Map.jsx`
**Responsabilidad**: Renderizar y manejar el mapa interactivo

**Props**:
- `origin`, `destination`: Coordenadas de origen y destino
- `onOriginChange`, `onDestinationChange`: Callbacks para cambios

**Métodos expuestos (vía ref)**:
- `getMap()`: Obtiene instancia de MapLibre
- `updateRoute(geojson)`: Actualiza ruta única
- `updateComparisonRoute(index, geojson, visible)`: Actualiza ruta de comparación
- `clearRoute()`: Limpia ruta única
- `clearComparisonRoutes()`: Limpia rutas de comparación
- `fitBounds(coordinates)`: Ajusta vista a coordenadas
- `flyTo(lon, lat, zoom)`: Anima a ubicación

**Características**:
- Marcadores arrastrables para origen/destino
- Click para colocar destino (Shift+click para origen)
- 3 capas de comparación con colores distintivos
- Controles de navegación integrados

---

### `SearchInput.jsx`
**Responsabilidad**: Input de búsqueda con autocompletado Nominatim

**Props**:
- `label`, `icon`: Etiqueta y emoji del campo
- `value`, `onChange`: Valor y callback del input
- `onSelect`: Callback al seleccionar resultado
- `onSearch`: Función de búsqueda
- `results`: Resultados del geocoding
- `placeholder`: Texto de placeholder

**Características**:
- Búsqueda con mínimo 3 caracteres
- Dropdown con hover effects
- Cierre automático al seleccionar
- Estilizado consistente con diseño dark

---

### `RouteControls.jsx`
**Responsabilidad**: Controles de configuración de ruta

**Props**:
- `origin`, `destination`: Coordenadas actuales
- `algorithm`, `optimization`: Valores seleccionados
- `loading`, `comparing`, `error`: Estados de UI
- `onOriginChange`, `onDestinationChange`: Callbacks de coordenadas
- `onAlgorithmChange`, `onOptimizationChange`: Callbacks de selectores
- `onCalculate`, `onCompare`: Callbacks de botones

**Elementos**:
- Inputs de coordenadas (lon, lat)
- Selector de algoritmo (6 opciones)
- Selector de optimización (4 tipos)
- Botón "Calcular ruta"
- Botón "Comparar algoritmos"
- Display de errores
- Hint de uso

---

### `RouteStats.jsx`
**Responsabilidad**: Mostrar estadísticas de ruta única

**Props**:
- `stats`: Objeto con estadísticas de la ruta

**Muestra**:
- Distancia total (km)
- Riesgo promedio
- Número de cámaras e incidentes
- Número de segmentos

---

### `ComparisonPanel.jsx`
**Responsabilidad**: Panel de comparación de múltiples rutas

**Props**:
- `results`: Array de rutas con estadísticas
- `visibleRoutes`: Objeto con visibilidad por algoritmo
- `onToggleVisibility`: Callback para mostrar/ocultar ruta

**Características**:
- Tarjetas clickeables por algoritmo
- Indicadores de color por ruta
- Estadísticas comparativas
- Estado visual de visibilidad
- Icons personalizados por algoritmo

---

## 🪝 Custom Hooks

### `useGeocoding()`
**Responsabilidad**: Manejar búsqueda de lugares

**Retorna**:
- `searchResults`: Array de resultados
- `searchLocation(query)`: Función de búsqueda
- `clearResults()`: Limpiar resultados

**Características**:
- Integración con Nominatim API
- Búsqueda acotada a Medellín
- Límite de 5 resultados
- Manejo de errores

---

### `useRouting()`
**Responsabilidad**: Manejar cálculo y comparación de rutas

**Retorna**:
- `loading`, `error`: Estados de UI
- `stats`: Estadísticas de ruta única
- `comparing`: Booleano de modo comparación
- `comparisonResults`: Array de rutas comparadas
- `visibleRoutes`: Visibilidad por algoritmo
- `calculateRoute(origin, dest, algo, opt)`: Calcular ruta
- `compareRoutes(origin, dest, opt)`: Comparar algoritmos
- `toggleRouteVisibility(algorithm)`: Toggle visibilidad
- `setError(msg)`: Setter de error

**Características**:
- Llamadas al backend `/route` y `/compare`
- Manejo de estados de carga
- Gestión de errores
- Toggle de visibilidad de rutas

---

## 🔄 Flujo de Datos

### Cálculo de Ruta Única
```
App.jsx
  └─> useRouting.calculateRoute()
       └─> POST /route
            └─> Update stats
                 └─> App.handleCalculateRoute()
                      └─> Map.updateRoute(geojson)
                           └─> Map.fitBounds()
```

### Comparación de Algoritmos
```
App.jsx
  └─> useRouting.compareRoutes()
       └─> POST /compare
            └─> Update comparisonResults
                 └─> App.handleCompareRoutes()
                      └─> Map.updateComparisonRoute(i, geojson)
                           └─> Map.fitBounds()
```

### Toggle de Visibilidad
```
ComparisonPanel (click)
  └─> App.handleToggleRouteVisibility()
       └─> useRouting.toggleRouteVisibility()
            └─> Update visibleRoutes state
                 └─> Map layers visibility updated
```

---

## 📊 Ventajas de la Refactorización

### ✅ Antes vs Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Líneas en App.jsx** | ~715 líneas | ~210 líneas |
| **Responsabilidades** | Todo en un archivo | Separadas por dominio |
| **Reusabilidad** | Componentes acoplados | Componentes independientes |
| **Testabilidad** | Difícil de testear | Hooks y componentes testeables |
| **Mantenibilidad** | Código espagueti | Estructura clara |
| **Legibilidad** | Estado mezclado con UI | Separación de concerns |

### 🎯 Principios Aplicados

1. **Single Responsibility**: Cada componente/hook tiene una sola responsabilidad
2. **Separation of Concerns**: Lógica separada de presentación
3. **DRY**: SearchInput reutilizable para origen y destino
4. **Composition**: App.jsx orquesta componentes pequeños
5. **Custom Hooks**: Lógica extraída y reutilizable

---

## 🔧 Cómo Usar

### Importar componentes
```jsx
import { Map, SearchInput, RouteControls } from './components'
```

### Importar hooks
```jsx
import { useGeocoding, useRouting } from './hooks'
```

### Usar ref del mapa
```jsx
const mapRef = useRef(null)

// Luego:
mapRef.current?.flyTo(lon, lat, zoom)
mapRef.current?.updateRoute(geojson)
```

---

## 📝 Notas de Migración

- El archivo `App.jsx.backup` contiene el código original
- Todos los componentes mantienen la misma funcionalidad
- Los estilos en `App.css` no cambiaron
- La API del backend no fue modificada

---

## 🚀 Próximos Pasos (Opcional)

1. Agregar PropTypes o TypeScript para type safety
2. Crear tests unitarios para hooks
3. Agregar tests de integración para componentes
4. Extraer constantes a archivo de configuración
5. Implementar context API para estado global
6. Agregar lazy loading de componentes
7. Implementar memoization con React.memo donde aplique
