/**
 * Componente para mostrar estadísticas de una ruta única
 */
export const RouteStats = ({ stats, performance, cost, algorithm }) => {
  if (!stats) return null

  return (
    <div>
      {/* Estadísticas de la ruta */}
      <div 
        className="group" 
        style={{
          marginTop: 16, 
          padding: 12, 
          background: 'rgba(124,58,237,0.08)', 
          borderRadius: 8, 
          border: '1px solid rgba(124,58,237,0.2)'
        }}
      >
        <label className="label">📊 Estadísticas de la ruta</label>
        <div style={{ fontSize: 13, lineHeight: 1.8, color: 'var(--text)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
            <span style={{ color: 'var(--muted)' }}>📏 Distancia total:</span>
            <strong>{(stats.total_distance / 1000).toFixed(2)} km</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
            <span style={{ color: 'var(--muted)' }}>🛡️ Riesgo promedio:</span>
            <strong>{isNaN(stats.avg_risk) ? 'N/A' : stats.avg_risk?.toFixed(4)}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
            <span style={{ color: 'var(--muted)' }}>📹 Cámaras en ruta:</span>
            <strong>{stats.total_cameras}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
            <span style={{ color: 'var(--muted)' }}>🚦 Incidentes en ruta:</span>
            <strong>{stats.total_incidents}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
            <span style={{ color: 'var(--muted)' }}>🔗 Segmentos:</span>
            <strong>{stats.num_segments}</strong>
          </div>
          {cost !== undefined && (
            <>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                padding: '4px 0',
                marginTop: 8,
                paddingTop: 8,
                borderTop: '1px solid rgba(124,58,237,0.2)'
              }}>
                <span style={{ color: 'var(--muted)' }}>💰 Costo optimizado:</span>
                <strong style={{ color: '#7c3aed' }}>{cost.toFixed(4)}</strong>
              </div>
              <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 4, fontStyle: 'italic' }}>
                (Valor según tipo de optimización elegida)
              </div>
            </>
          )}
        </div>
      </div>

      {/* Métricas de rendimiento */}
      {performance && (
        <div 
          className="group" 
          style={{
            marginTop: 12, 
            padding: 12, 
            background: 'rgba(251,146,60,0.08)', 
            borderRadius: 8, 
            border: '1px solid rgba(251,146,60,0.2)'
          }}
        >
          <label className="label">⚡ Métricas de Rendimiento</label>
          {algorithm && (
            <div style={{ 
              fontSize: 11, 
              color: 'var(--muted)', 
              marginBottom: 8,
              fontStyle: 'italic'
            }}>
              Algoritmo: <strong style={{ color: 'var(--text)' }}>{algorithm}</strong>
            </div>
          )}
          <div style={{ fontSize: 13, lineHeight: 1.8, color: 'var(--text)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ color: 'var(--muted)' }}>⏱️ Tiempo de ejecución:</span>
              <strong style={{ color: '#fb923c' }}>{performance.execution_time_ms?.toFixed(2)} ms</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ color: 'var(--muted)' }}>🔍 Nodos explorados:</span>
              <strong>{performance.nodes_explored}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ color: 'var(--muted)' }}>🛤️ Nodos en la ruta:</span>
              <strong>{performance.nodes_in_path}</strong>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
