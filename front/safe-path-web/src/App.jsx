import { useRef, useState } from 'react'
import './App.css'
import { Map, SearchInput, RouteControls, RouteStats, ComparisonPanel } from './components'
import { useGeocoding, useRouting } from './hooks'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const mapRef = useRef(null)
  
  // State
  const [origin, setOrigin] = useState({ lon: -75.5657, lat: 6.2080 })
  const [destination, setDestination] = useState({ lon: -75.5676, lat: 6.2528 })
  const [originSearch, setOriginSearch] = useState('')
  const [destSearch, setDestSearch] = useState('')
  const [algorithm, setAlgorithm] = useState('dijkstra')
  const [optimization, setOptimization] = useState('combined')

  // Custom hooks
  const originGeocoding = useGeocoding()
  const destGeocoding = useGeocoding()
  const routing = useRouting()

  // Current map center as focus point for geocoding
  const getFocusPoint = () => {
    const center = mapRef.current?.getMap()?.getCenter?.()
    if (center && typeof center.lng === 'number' && typeof center.lat === 'number') {
      return { lon: center.lng, lat: center.lat }
    }
    // Fallback to current origin if map not ready
    if (origin && typeof origin.lon === 'number' && typeof origin.lat === 'number') {
      return { lon: origin.lon, lat: origin.lat }
    }
    return { lon: -75.5657, lat: 6.2080 }
  }

  // Handlers para geocoding
  const handleSelectOrigin = (place) => {
    const lon = parseFloat(place.lon)
    const lat = parseFloat(place.lat)
    setOrigin({ lon, lat })
    setOriginSearch(place.display_name.split(',')[0])
    originGeocoding.clearResults()
    mapRef.current?.flyTo(lon, lat, 15)
  }

  const handleSelectDestination = (place) => {
    const lon = parseFloat(place.lon)
    const lat = parseFloat(place.lat)
    setDestination({ lon, lat })
    setDestSearch(place.display_name.split(',')[0])
    destGeocoding.clearResults()
    mapRef.current?.flyTo(lon, lat, 15)
  }

  // Handler para calcular ruta individual
  const handleCalculateRoute = async () => {
    const data = await routing.calculateRoute(origin, destination, algorithm, optimization)
    
    if (!data) return

    // Clear comparison routes
    mapRef.current?.clearComparisonRoutes()
    
    // Update single route on map
    const geojson = {
      type: 'FeatureCollection',
      features: data.features || []
    }
    mapRef.current?.updateRoute(geojson)
    
    // Fit bounds to route
    if (data.features && data.features.length > 0) {
      const coordinates = []
      data.features.forEach(f => {
        if (f.geometry?.type === 'LineString') {
          coordinates.push(...f.geometry.coordinates)
        }
      })
      if (coordinates.length > 0) {
        mapRef.current?.fitBounds(coordinates)
      }
    }
  }

  // Handler para comparar algoritmos
  const handleCompareRoutes = async () => {
    const data = await routing.compareRoutes(origin, destination, optimization)
    
    if (!data) return

    // Clear single route
    mapRef.current?.clearRoute()
    
    // Update comparison routes on map
    const allCoordinates = []

    // Map fixed algorithm -> layer index for consistent colors
    const algIndex = { dijkstra: 0, greedy: 1, branch_and_bound: 2 }

    // First, clear and hide all compare sources
    const map = mapRef.current?.getMap()
    if (map) {
      for (let i = 0; i < 3; i++) {
        const empty = { type: 'FeatureCollection', features: [] }
        mapRef.current?.updateComparisonRoute(i, empty, false)
      }
    }

    // Place each returned route into its fixed slot
    data.routes.forEach((route) => {
      const idx = algIndex[route.algorithm] ?? -1
      if (idx === -1) return

      if (route.features && route.features.length > 0) {
        const geojson = {
          type: 'FeatureCollection',
          features: route.features
        }
        mapRef.current?.updateComparisonRoute(idx, geojson, true)

        // Collect coordinates for bounds
        route.features.forEach(f => {
          if (f.geometry?.type === 'LineString') {
            allCoordinates.push(...f.geometry.coordinates)
          }
        })
      }
    })
    
    // Fit bounds to all routes
    if (allCoordinates.length > 0) {
      mapRef.current?.fitBounds(allCoordinates)
    }
  }

  // Handler para toggle de visibilidad de rutas en comparación
  const handleToggleRouteVisibility = (algorithm) => {
    routing.toggleRouteVisibility(algorithm)
    
    // Update map layer visibility
    const index = ['dijkstra', 'greedy', 'branch_and_bound'].indexOf(algorithm)
    if (index !== -1) {
      const newVisibility = !routing.visibleRoutes[algorithm]
      
      // Get current route data to preserve it
      const map = mapRef.current?.getMap()
      if (map) {
        const lineId = `compare-line-${index}`
        const glowId = `compare-glow-${index}`
        
        const visibility = newVisibility ? 'visible' : 'none'
        if (map.getLayer(lineId)) {
          map.setLayoutProperty(lineId, 'visibility', visibility)
        }
        if (map.getLayer(glowId)) {
          map.setLayoutProperty(glowId, 'visibility', visibility)
        }
      }
    }
  }

  return (
    <div className="app-root">
      <div className="app-header">
        <div className="brand">
          <div className="logo-dot" />
          <div>
            <h1>SafePath</h1>
            <p className="subtitle">Rutas seguras en Medellín</p>
          </div>
        </div>
      </div>

      <div className="layout">
        <div className="controls">
          {/* Búsqueda de origen */}
          <SearchInput
            label="Buscar origen"
            icon="🔍"
            value={originSearch}
            onChange={setOriginSearch}
            onSelect={handleSelectOrigin}
            onSearch={(q, fp) => originGeocoding.searchLocation(q, fp || getFocusPoint())}
            results={originGeocoding.searchResults}
            placeholder="Ej: Parque Lleras"
            focusPoint={getFocusPoint()}
          />

          {/* Búsqueda de destino */}
          <SearchInput
            label="Buscar destino"
            icon="🎯"
            value={destSearch}
            onChange={setDestSearch}
            onSelect={handleSelectDestination}
            onSearch={(q, fp) => destGeocoding.searchLocation(q, fp || getFocusPoint())}
            results={destGeocoding.searchResults}
            placeholder="Ej: Metro Poblado"
            focusPoint={getFocusPoint()}
          />

          {/* Controles de ruta */}
          <RouteControls
            origin={origin}
            destination={destination}
            algorithm={algorithm}
            optimization={optimization}
            loading={routing.loading}
            comparing={routing.comparing}
            error={routing.error}
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onAlgorithmChange={setAlgorithm}
            onOptimizationChange={setOptimization}
            onCalculate={handleCalculateRoute}
            onCompare={handleCompareRoutes}
          />

          {/* Estadísticas o comparación */}
          {routing.comparing ? (
            <ComparisonPanel
              results={routing.comparisonResults}
              visibleRoutes={routing.visibleRoutes}
              onToggleVisibility={handleToggleRouteVisibility}
            />
          ) : (
            <RouteStats stats={routing.stats} />
          )}
        </div>

        {/* Mapa */}
        <Map
          ref={mapRef}
          origin={origin}
          destination={destination}
          onOriginChange={setOrigin}
          onDestinationChange={setDestination}
        />
      </div>
    </div>
  )
}
