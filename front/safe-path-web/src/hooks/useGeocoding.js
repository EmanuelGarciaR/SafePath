import { useState } from 'react'

/**
 * Hook para manejar búsqueda de lugares con Nominatim API
 */
export const useGeocoding = () => {
  const [searchResults, setSearchResults] = useState([])

  // In-memory cache to avoid repeated queries
  const cache = new Map()
  let abortController = null
  let debounceTimer = null

  const rankResults = (items, q, focus) => {
    const query = (q || '').toLowerCase()
    return items
      .map((it) => {
        const name = (it.display_name || '').toLowerCase()
        const addr = it.address || {}
        const importance = Number(it.importance || 0)
        const type = it.type || it.category || ''
        const inMedellin = [addr.city, addr.town, addr.county, addr.municipality].filter(Boolean).some(v => (v || '').toLowerCase().includes('medellín') || (v || '').toLowerCase().includes('medellin'))
        const inAntioquia = (addr.state || '').toLowerCase().includes('antioquia')
        const starts = name.startsWith(query)
        const contains = name.includes(query)

        let score = 0
        score += importance * 50
        if (inMedellin) score += 20
        if (inAntioquia) score += 10
        const preferredTypes = new Set(['neighbourhood','suburb','road','residential','primary','secondary','tertiary','unclassified','commercial','industrial','attraction','amenity','tourism','university','school','hospital','parking','supermarket'])
        if (preferredTypes.has(type)) score += 10
        if (starts) score += 12
        else if (contains) score += 5

        // Proximity bias if a focus point is provided
        if (focus && typeof focus.lon === 'number' && typeof focus.lat === 'number') {
          const lon = parseFloat(it.lon)
          const lat = parseFloat(it.lat)
          if (!isNaN(lon) && !isNaN(lat)) {
            // rough meters distance
            const dx = (lon - focus.lon) * 111000 * Math.cos((((lat + focus.lat) / 2) * Math.PI) / 180)
            const dy = (lat - focus.lat) * 111000
            const dist = Math.sqrt(dx*dx + dy*dy) // meters
            // subtract up to ~15 points beyond 2km
            score -= Math.max(0, Math.min(15, (dist - 2000) / 250))
          }
        }

        return { ...it, _score: score }
      })
      .sort((a, b) => b._score - a._score)
  }

  const searchLocation = async (query, focus) => {
    if (!query || query.length < 3) {
      setSearchResults([])
      return []
    }

    const key = `${query}|${focus?.lon ?? ''},${focus?.lat ?? ''}`
    if (cache.has(key)) {
      const cached = cache.get(key)
      setSearchResults(cached)
      return cached
    }

    // Debounce
    if (debounceTimer) clearTimeout(debounceTimer)

    return await new Promise((resolve) => {
      debounceTimer = setTimeout(async () => {
        // Cancel previous request if any
        if (abortController) abortController.abort()
        abortController = new AbortController()

        try {
          const params = new URLSearchParams({
            format: 'jsonv2',
            addressdetails: '1',
            namedetails: '1',
            limit: '8',
            'accept-language': 'es',
            countrycodes: 'co',
            viewbox: '-75.7,6.1,-75.4,6.4',
            bounded: '1',
            q: `${query}, Medellín, Colombia`
          })

          const url = `https://nominatim.openstreetmap.org/search?${params.toString()}`
          const response = await fetch(url, {
            headers: {
              'User-Agent': 'SafePath Medellin (educational app)'
            },
            signal: abortController.signal
          })
          const raw = await response.json()
          const ranked = rankResults(Array.isArray(raw) ? raw : [], query, focus)
          cache.set(key, ranked)
          setSearchResults(ranked)
          resolve(ranked)
        } catch (error) {
          if (error?.name !== 'AbortError') {
            console.error('Error en geocoding:', error)
            setSearchResults([])
            resolve([])
          }
        }
      }, 250)
    })
  }

  const clearResults = () => {
    setSearchResults([])
  }

  return {
    searchResults,
    searchLocation,
    clearResults
  }
}
