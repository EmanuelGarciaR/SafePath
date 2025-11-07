import { useState, useEffect } from 'react'

/**
 * Componente para búsqueda de lugares con autocompletado
 */
export const SearchInput = ({ 
  label, 
  icon, 
  value, 
  onChange, 
  onSelect, 
  onSearch, 
  results = [],
  placeholder = "Buscar lugar...",
  focusPoint
}) => {
  const [showResults, setShowResults] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const [debounceTimer, setDebounceTimer] = useState(null)

  const handleInputChange = async (e) => {
    const query = e.target.value
    onChange(query)
    
    // Limpiar timer anterior
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    
    if (query.length >= 3) {
      // Esperar 400ms después de que el usuario deje de escribir
      const timer = setTimeout(async () => {
        await onSearch(query, focusPoint)
        setShowResults(true)
        setActiveIndex(-1)
      }, 400)
      setDebounceTimer(timer)
    } else {
      setShowResults(false)
      setActiveIndex(-1)
    }
  }

  const handleSelectPlace = (place) => {
    // Limpiar timer pendiente al seleccionar
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    onSelect(place)
    setShowResults(false)
    setActiveIndex(-1)
  }

  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
    }
  }, [debounceTimer])

  const handleKeyDown = async (e) => {
    if (!showResults && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      setShowResults(true)
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((prev) => Math.min((prev < 0 ? 0 : prev + 1), Math.max(0, results.length - 1)))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((prev) => Math.max(-1, prev - 1))
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < results.length) {
        handleSelectPlace(results[activeIndex])
      }
    } else if (e.key === 'Escape') {
      setShowResults(false)
      setActiveIndex(-1)
    }
  }

  return (
    <div className="group" style={{ position: 'relative' }}>
      <label className="label">{icon} {label}</label>
      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={(e) => {
          e.target.style.borderColor = 'var(--acc-1)'
          if (results.length > 0) setShowResults(true)
        }}
        onBlur={(e) => {
          e.target.style.borderColor = 'rgba(255,255,255,0.1)'
          setTimeout(() => setShowResults(false), 200)
        }}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '8px 12px',
          fontSize: 14,
          background: 'var(--bg)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 6,
          color: 'var(--text)',
          outline: 'none',
          transition: 'border-color 0.2s'
        }}
      />
      
      {showResults && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          marginTop: 4,
          background: 'var(--panel)',
          border: '1px solid rgba(255,255,255,0.15)',
          borderRadius: 6,
          maxHeight: 240,
          overflowY: 'auto',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
        }}>
          {results.length === 0 ? (
            <div style={{ padding: '10px 12px', fontSize: 12, color: 'var(--muted)' }}>
              Sin resultados. Intenta con otro término.
            </div>
          ) : results.map((place, idx) => {
            const title = place.display_name.split(',')[0]
            const subtitle = place.display_name.split(',').slice(1, 3).join(',')
            const isActive = idx === activeIndex
            return (
              <div
                key={idx}
                onClick={() => handleSelectPlace(place)}
                style={{
                  padding: '10px 12px',
                  fontSize: 13,
                  cursor: 'pointer',
                  borderBottom: idx < results.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                  transition: 'background 0.15s',
                  background: isActive ? 'rgba(124,58,237,0.2)' : 'transparent'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(124,58,237,0.15)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = isActive ? 'rgba(124,58,237,0.2)' : 'transparent'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 16 }}>📍</span>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text)' }}>{title}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>{subtitle}</div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
