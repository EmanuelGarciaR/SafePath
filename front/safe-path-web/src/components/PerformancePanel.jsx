/**
 * Componente para mostrar métricas de rendimiento de algoritmos
 */
export const PerformancePanel = ({ results }) => {
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

  // Encontrar el mejor en cada métrica
  const bestTime = Math.min(...results.map(r => r.performance?.execution_time_ms || Infinity))
  const bestNodes = Math.min(...results.map(r => r.performance?.nodes_explored || Infinity))
  const bestCost = Math.min(...results.map(r => r.cost || Infinity))

  return (
    <div 
      className="group" 
      style={{
        marginTop: 16, 
        padding: 12, 
        background: 'rgba(251,146,60,0.08)', 
        borderRadius: 8, 
        border: '1px solid rgba(251,146,60,0.2)'
      }}
    >
      <label className="label">⚡ Métricas de Rendimiento</label>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(3, 1fr)', 
        gap: 8, 
        marginTop: 10,
        fontSize: 11,
        fontWeight: 600,
        color: 'var(--muted)',
        textAlign: 'center'
      }}>
        <div>⏱️ Tiempo</div>
        <div>🔍 Nodos revisados</div>
        <div>💰 Costo óptimo</div>
      </div>

      {results.map((route, index) => {
        const perf = route.performance || {}
        const time = perf.execution_time_ms || 0
        const nodes = perf.nodes_explored || 0
        const cost = route.cost || 0

        const isBestTime = time === bestTime && time > 0
        const isBestNodes = nodes === bestNodes && nodes > 0
        const isBestCost = cost === bestCost && cost > 0

        return (
          <div 
            key={route.algorithm}
            style={{
              marginTop: 10,
              padding: 10,
              background: 'rgba(255,255,255,0.03)',
              borderRadius: 6,
              border: `2px solid ${colors[index]}`,
            }}
          >
            <div style={{
              display: 'flex', 
              alignItems: 'center', 
              gap: 6,
              marginBottom: 8
            }}>
              <div style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: colors[index],
                border: '2px solid white'
              }}/>
              <strong style={{ fontSize: 13 }}>
                {icons[route.algorithm] || '🔹'} {names[route.algorithm] || route.algorithm}
              </strong>
            </div>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(3, 1fr)', 
              gap: 8,
              fontSize: 12,
              textAlign: 'center'
            }}>
              <div style={{
                padding: '6px 4px',
                background: isBestTime ? 'rgba(34,197,94,0.15)' : 'rgba(0,0,0,0.2)',
                borderRadius: 4,
                border: isBestTime ? '1px solid rgba(34,197,94,0.4)' : 'none'
              }}>
                <div style={{ fontWeight: 600, color: isBestTime ? '#22c55e' : 'var(--text)' }}>
                  {time.toFixed(1)}
                </div>
                <div style={{ fontSize: 10, color: 'var(--muted)' }}>ms</div>
                {isBestTime && <div style={{ fontSize: 9, color: '#22c55e' }}>⚡ Más rápido</div>}
              </div>

              <div style={{
                padding: '6px 4px',
                background: isBestNodes ? 'rgba(34,197,94,0.15)' : 'rgba(0,0,0,0.2)',
                borderRadius: 4,
                border: isBestNodes ? '1px solid rgba(34,197,94,0.4)' : 'none'
              }}>
                <div style={{ fontWeight: 600, color: isBestNodes ? '#22c55e' : 'var(--text)' }}>
                  {nodes}
                </div>
                <div style={{ fontSize: 10, color: 'var(--muted)' }}>nodos</div>
                {isBestNodes && <div style={{ fontSize: 9, color: '#22c55e' }}>🎯 Más eficiente</div>}
              </div>

              <div style={{
                padding: '6px 4px',
                background: isBestCost ? 'rgba(34,197,94,0.15)' : 'rgba(0,0,0,0.2)',
                borderRadius: 4,
                border: isBestCost ? '1px solid rgba(34,197,94,0.4)' : 'none'
              }}>
                <div style={{ fontWeight: 600, color: isBestCost ? '#22c55e' : 'var(--text)' }}>
                  {cost.toFixed(2)}
                </div>
                <div style={{ fontSize: 10, color: 'var(--muted)' }}>costo</div>
                {isBestCost && <div style={{ fontSize: 9, color: '#22c55e' }}>💎 Óptimo</div>}
              </div>
            </div>
          </div>
        )
      })}
      
      <div style={{
        marginTop: 12, 
        fontSize: 10, 
        color: 'var(--muted)', 
        fontStyle: 'italic',
        textAlign: 'center',
        lineHeight: 1.4
      }}>
        💡 <strong style={{ color: 'var(--text)' }}>Costo</strong> = valor total según optimización elegida (distancia en m, índice de riesgo, combinado, o incidentes)
        <br/>
        <strong style={{ color: 'var(--text)' }}>Nodos revisados</strong> = cuántos nodos exploró el algoritmo durante la búsqueda
      </div>
    </div>
  )
}
