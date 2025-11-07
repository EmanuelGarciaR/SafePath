/**
 * Componente para controles de ruta (coordenadas, algoritmo, botones)
 */
export const RouteControls = ({
  origin,
  destination,
  algorithm,
  optimization,
  loading,
  comparing,
  error,
  onOriginChange,
  onDestinationChange,
  onAlgorithmChange,
  onOptimizationChange,
  onCalculate,
  onCompare
}) => {
  return (
    <>
      {/* Coordenadas de origen */}
      <div className="group">
        <label className="label">📍 Coordenadas de Origen</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="number"
            step="0.000001"
            placeholder="Longitud"
            value={origin.lon}
            onChange={(e) => onOriginChange({ ...origin, lon: e.target.value })}
            style={{ flex: 1 }}
          />
          <input
            type="number"
            step="0.000001"
            placeholder="Latitud"
            value={origin.lat}
            onChange={(e) => onOriginChange({ ...origin, lat: e.target.value })}
            style={{ flex: 1 }}
          />
        </div>
      </div>

      {/* Coordenadas de destino */}
      <div className="group">
        <label className="label">🎯 Coordenadas de Destino</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="number"
            step="0.000001"
            placeholder="Longitud"
            value={destination.lon}
            onChange={(e) => onDestinationChange({ ...destination, lon: e.target.value })}
            style={{ flex: 1 }}
          />
          <input
            type="number"
            step="0.000001"
            placeholder="Latitud"
            value={destination.lat}
            onChange={(e) => onDestinationChange({ ...destination, lat: e.target.value })}
            style={{ flex: 1 }}
          />
        </div>
      </div>

      {/* Selector de algoritmo */}
      <div className="group">
        <label className="label">🧮 Algoritmo</label>
        <select 
          value={algorithm} 
          onChange={(e) => onAlgorithmChange(e.target.value)}
        >
          <optgroup label="Clásicos">
            <option value="dijkstra">Dijkstra</option>
            <option value="astar">A* (A-Star)</option>
            <option value="bellman_ford">Bellman-Ford</option>
          </optgroup>
          <optgroup label="Experimentales">
            <option value="greedy">Greedy</option>
            <option value="backtracking">Backtracking</option>
            <option value="branch_and_bound">Branch & Bound</option>
          </optgroup>
        </select>
      </div>

      {/* Tipo de optimización */}
      <div className="group">
        <label className="label">🎚️ Optimización</label>
        <select 
          value={optimization} 
          onChange={(e) => onOptimizationChange(e.target.value)}
        >
          <option value="distance">Distancia</option>
          <option value="risk">Riesgo (seguridad)</option>
          <option value="combined">Combinado</option>
          <option value="incidents">Incidentes</option>
        </select>
      </div>

      {/* Botones de acción */}
      <button 
        className="primary" 
        onClick={onCalculate} 
        disabled={loading}
      >
        {loading && !comparing ? '⏳ Calculando...' : '🧭 Calcular ruta'}
      </button>

      <button 
        className="primary" 
        onClick={onCompare} 
        disabled={loading}
        style={{
          marginTop: 8,
          background: 'linear-gradient(90deg, #10b981, #06b6d4)',
          boxShadow: '0 10px 30px rgba(16,185,129,.25)'
        }}
      >
        {loading && comparing ? '⏳ Comparando...' : '⚖️ Comparar algoritmos'}
      </button>

      {/* Error */}
      {error && <div className="error">❌ {error}</div>}

      {/* Hint */}
      <div style={{
        marginTop: 16,
        padding: 10,
        fontSize: 12,
        color: 'var(--muted)',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: 6,
        border: '1px solid rgba(255,255,255,0.05)'
      }}>
        💡 <em>Puedes buscar por nombre o ingresar coordenadas manualmente</em>
      </div>
    </>
  )
}
