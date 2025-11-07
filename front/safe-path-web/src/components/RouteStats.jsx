/**
 * Componente para mostrar estadísticas de una ruta única
 */
export const RouteStats = ({ stats }) => {
  if (!stats) return null

  return (
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
        <div><strong>Distancia:</strong> {(stats.total_distance / 1000).toFixed(2)} km</div>
        <div><strong>Riesgo promedio:</strong> {stats.avg_risk?.toFixed(3)}</div>
        <div>
          <strong>Cámaras:</strong> {stats.total_cameras} · <strong>Incidentes:</strong> {stats.total_incidents}
        </div>
        <div><strong>Segmentos:</strong> {stats.num_segments}</div>
      </div>
    </div>
  )
}
