/**
 * Componente para mostrar comparación de múltiples rutas
 */
export const ComparisonPanel = ({ results, visibleRoutes, onToggleVisibility }) => {
  if (!results || results.length === 0) return null

  const colors = ['#7c3aed', '#10b981', '#f59e0b']
  const icons = {
    'dijkstra': '🏆',
    'greedy': '🌱',
    'branch_and_bound': '🌳',
    'bellman_ford': '🔄',
    'backtracking': '🔙'
  }

  const names = {
    'dijkstra': 'Dijkstra',
    'greedy': 'Greedy',
    'branch_and_bound': 'Branch & Bound',
    'bellman_ford': 'Bellman-Ford',
    'backtracking': 'Backtracking'
  }

  return (
    <div 
      className="group" 
      style={{
        marginTop: 16, 
        padding: 12, 
        background: 'rgba(6,182,212,0.08)', 
        borderRadius: 8, 
        border: '1px solid rgba(6,182,212,0.2)'
      }}
    >
      <label className="label">⚖️ Comparación de rutas</label>
      
      {results.map((route, index) => {
        const isVisible = visibleRoutes[route.algorithm]
        
        return (
          <div 
            key={route.algorithm}
            style={{
              marginTop: 10,
              padding: 10,
              background: isVisible ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.2)',
              borderRadius: 6,
              border: `2px solid ${colors[index]}`,
              cursor: 'pointer',
              opacity: isVisible ? 1 : 0.5,
              transition: 'all 0.2s'
            }}
            onClick={() => onToggleVisibility(route.algorithm)}
          >
            <div style={{
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              marginBottom: 6
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  background: colors[index],
                  border: '2px solid white'
                }}/>
                <strong>
                  {icons[route.algorithm] || '🔹'} {names[route.algorithm] || route.algorithm.toUpperCase()}
                </strong>
                {route.note && (
                  <span style={{
                    marginLeft: 8,
                    fontSize: 11,
                    color: '#bbb',
                    fontStyle: 'italic'
                  }}>
                    ({route.note})
                  </span>
                )}
              </div>
              <span style={{ fontSize: 11, color: '#888' }}>
                {isVisible ? '👁️ Visible' : '🚫 Oculta'}
              </span>
            </div>
            
            <div style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--muted)' }}>
              <div>📏 Distancia: {(route.statistics.total_distance / 1000).toFixed(2)} km ({route.statistics.num_segments} segmentos)</div>
              <div>🛡️ Riesgo: {isNaN(route.statistics.avg_risk) ? 'N/A' : route.statistics.avg_risk.toFixed(4)}</div>
              <div>
                📹 {route.statistics.total_cameras} cámaras · 
                🚦 {route.statistics.total_incidents} incidentes
              </div>
              <div style={{ marginTop: 4, paddingTop: 4, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                💰 Costo: <strong>{route.cost.toFixed(2)}</strong>
              </div>
            </div>
          </div>
        )
      })}
      
      <div style={{
        marginTop: 12, 
        fontSize: 11, 
        color: 'var(--muted)', 
        fontStyle: 'italic'
      }}>
        💡 Click en cada ruta para mostrar/ocultar en el mapa
      </div>
    </div>
  )
}
