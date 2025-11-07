import { useState } from 'react'

const API_BASE = import.meta.env?.VITE_API_BASE || 'http://localhost:8000'

/**
 * Hook para manejar cálculo de rutas y comparaciones
 */
export const useRouting = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [performance, setPerformance] = useState(null)
  const [cost, setCost] = useState(null)
  const [algorithm, setAlgorithm] = useState(null)
  const [comparing, setComparing] = useState(false)
  const [comparisonResults, setComparisonResults] = useState([])
  const [visibleRoutes, setVisibleRoutes] = useState({
    'dijkstra': true,
    'greedy': true,
    'branch_and_bound': true
  })

  const calculateRoute = async (origin, destination, algorithm, optimization) => {
    setLoading(true)
    setError(null)
    setComparing(false)
    setComparisonResults([])

    try {
      const qs = new URLSearchParams({
        origin_lon: String(origin.lon),
        origin_lat: String(origin.lat),
        dest_lon: String(destination.lon),
        dest_lat: String(destination.lat),
        optimization: String(optimization),
        algorithm: String(algorithm)
      })
      const response = await fetch(`${API_BASE}/route?${qs.toString()}`)

      const data = await response.json()

      if (!response.ok || !data.features || data.features.length === 0) {
        throw new Error(data.detail || 'No se encontró una ruta válida')
      }

      setStats(data?.properties?.statistics || null)
      setPerformance(data?.properties?.performance || null)
      setCost(data?.properties?.cost || null)
      setAlgorithm(data?.properties?.algorithm || algorithm)
      return data
    } catch (err) {
      setError(err.message || 'Error al calcular la ruta')
      return null
    } finally {
      setLoading(false)
    }
  }

  const compareRoutes = async (origin, destination, optimization) => {
    setLoading(true)
    setError(null)
    setComparing(true)
    setStats(null)

    try {
      const qs = new URLSearchParams({
        origin_lon: String(origin.lon),
        origin_lat: String(origin.lat),
        dest_lon: String(destination.lon),
        dest_lat: String(destination.lat),
        optimization: String(optimization),
        algorithms: 'dijkstra,greedy,branch_and_bound'
      })
      const response = await fetch(`${API_BASE}/compare?${qs.toString()}`)

      const data = await response.json()

      if (!response.ok || !data.routes || data.routes.length === 0) {
        throw new Error(data.detail || 'No se pudo realizar la comparación')
      }

      setComparisonResults(data.routes)
      return data
    } catch (err) {
      setError(err.message || 'Error al comparar rutas')
      return null
    } finally {
      setLoading(false)
    }
  }

  const toggleRouteVisibility = (algorithm) => {
    setVisibleRoutes(prev => ({
      ...prev,
      [algorithm]: !prev[algorithm]
    }))
  }

  return {
    loading,
    error,
    stats,
    performance,
    cost,
    algorithm,
    comparing,
    comparisonResults,
    visibleRoutes,
    calculateRoute,
    compareRoutes,
    toggleRouteVisibility,
    setError
  }
}
