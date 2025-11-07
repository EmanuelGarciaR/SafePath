import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react'
import maplibregl from 'maplibre-gl'

/**
 * Componente de mapa con MapLibre GL
 */
export const Map = forwardRef(({ origin, destination, onOriginChange, onDestinationChange }, ref) => {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const originMarkerRef = useRef(null)
  const destMarkerRef = useRef(null)

  // Exponer métodos del mapa al componente padre
  useImperativeHandle(ref, () => ({
    getMap: () => mapRef.current,
    updateRoute: (geojson) => {
      const map = mapRef.current
      if (!map) return
      
      const source = map.getSource('route')
      if (source) {
        source.setData(geojson)
      }
    },
    updateComparisonRoute: (index, geojson, visible = true) => {
      const map = mapRef.current
      if (!map) return
      
      const sourceId = `compare-route-${index}`
      const lineId = `compare-line-${index}`
      const glowId = `compare-glow-${index}`
      
      const source = map.getSource(sourceId)
      if (source) {
        source.setData(geojson)
      }
      
      const visibility = visible ? 'visible' : 'none'
      if (map.getLayer(lineId)) {
        map.setLayoutProperty(lineId, 'visibility', visibility)
      }
      if (map.getLayer(glowId)) {
        map.setLayoutProperty(glowId, 'visibility', visibility)
      }
    },
    clearRoute: () => {
      const map = mapRef.current
      if (!map) return
      
      const emptyData = { type: 'FeatureCollection', features: [] }
      const source = map.getSource('route')
      if (source) {
        source.setData(emptyData)
      }
    },
    clearComparisonRoutes: () => {
      const map = mapRef.current
      if (!map) return
      
      const emptyData = { type: 'FeatureCollection', features: [] }
      for (let i = 0; i < 3; i++) {
        const source = map.getSource(`compare-route-${i}`)
        if (source) {
          source.setData(emptyData)
        }
      }
    },
    fitBounds: (coordinates) => {
      const map = mapRef.current
      if (!map || !coordinates || coordinates.length === 0) return
      
      const bounds = coordinates.reduce((bounds, coord) => {
        return bounds.extend(coord)
      }, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]))
      
      map.fitBounds(bounds, { padding: 50, duration: 1000 })
    },
    flyTo: (lon, lat, zoom = 14) => {
      const map = mapRef.current
      if (!map) return
      
      map.flyTo({ center: [lon, lat], zoom, duration: 1500 })
    }
  }))

  useEffect(() => {
    if (mapRef.current) return
    
    const timer = setTimeout(() => {
      console.log('Initializing map...')
      
      const map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: {
          version: 8,
          glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
          sources: {
            osm: {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '&copy; OpenStreetMap contributors'
            }
          },
          layers: [
            {
              id: 'background',
              type: 'background',
              paint: { 'background-color': '#0a0e1a' }
            },
            {
              id: 'osm',
              type: 'raster',
              source: 'osm',
              paint: {
                'raster-opacity': 0.6,
                'raster-brightness-min': 0.3,
                'raster-brightness-max': 0.7,
                'raster-contrast': 0.2,
                'raster-saturation': -0.3
              }
            }
          ]
        },
        center: [-75.57, 6.24],
        zoom: 12
      })
      
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
      mapRef.current = map

      map.on('load', () => {
        console.log('✅ Map loaded!')
        
        // Single route source and layers
        map.addSource('route', { 
          type: 'geojson', 
          data: { type: 'FeatureCollection', features: [] } 
        })
        
        map.addLayer({
          id: 'route-glow',
          type: 'line',
          source: 'route',
          paint: {
            'line-color': '#a78bfa',
            'line-width': ['interpolate', ['linear'], ['zoom'], 10, 8, 14, 16],
            'line-opacity': 0.3,
            'line-blur': 2
          }
        })
        
        map.addLayer({
          id: 'route-line',
          type: 'line',
          source: 'route',
          paint: {
            'line-color': ['interpolate', ['linear'], ['zoom'], 10, '#7c3aed', 14, '#06b6d4'],
            'line-width': ['interpolate', ['linear'], ['zoom'], 10, 4, 14, 8],
            'line-opacity': 1
          }
        })

        // Comparison route sources and layers
        const comparisonColors = [
          { main: '#7c3aed', glow: '#a78bfa' }, // purple (astar)
          { main: '#10b981', glow: '#6ee7b7' }, // green (greedy)
          { main: '#f59e0b', glow: '#fbbf24' }  // orange (dijkstra)
        ]
        
        for (let i = 0; i < 3; i++) {
          const sourceId = `compare-route-${i}`
          const lineId = `compare-line-${i}`
          const glowId = `compare-glow-${i}`
          
          map.addSource(sourceId, {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] }
          })
          
          map.addLayer({
            id: glowId,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': comparisonColors[i].glow,
              'line-width': ['interpolate', ['linear'], ['zoom'], 10, 8, 14, 16],
              'line-opacity': 0.25,
              'line-blur': 2
            }
          })
          
          map.addLayer({
            id: lineId,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': comparisonColors[i].main,
              'line-width': ['interpolate', ['linear'], ['zoom'], 10, 4, 14, 8],
              'line-opacity': 0.9
            }
          })
        }

        // Create markers
        const makeMarkerEl = (bg) => {
          const el = document.createElement('div')
          el.style.width = '16px'
          el.style.height = '16px'
          el.style.borderRadius = '50%'
          el.style.boxShadow = `0 0 0 3px rgba(255,255,255,.8) inset, 0 0 20px ${bg === '#7c3aed' ? 'rgba(124,58,237,.8)' : 'rgba(6,182,212,.8)'}`
          el.style.background = bg
          el.style.border = '2px solid white'
          el.style.cursor = 'grab'
          return el
        }

        // Origin marker
        const originMarker = new maplibregl.Marker({
          element: makeMarkerEl('#7c3aed'), 
          draggable: true
        })
          .setLngLat([origin.lon, origin.lat])
          .addTo(map)
        
        originMarker.on('dragend', () => {
          const { lng, lat } = originMarker.getLngLat()
          onOriginChange({ lon: lng, lat })
        })
        originMarkerRef.current = originMarker

        // Destination marker
        const destMarker = new maplibregl.Marker({
          element: makeMarkerEl('#06b6d4'), 
          draggable: true
        })
          .setLngLat([destination.lon, destination.lat])
          .addTo(map)
        
        destMarker.on('dragend', () => {
          const { lng, lat } = destMarker.getLngLat()
          onDestinationChange({ lon: lng, lat })
        })
        destMarkerRef.current = destMarker

        // Click to set destination (Shift+click for origin)
        map.on('click', (e) => {
          const { lng, lat } = e.lngLat
          if (e.originalEvent.shiftKey) {
            onOriginChange({ lon: lng, lat })
            originMarkerRef.current?.setLngLat([lng, lat])
          } else {
            onDestinationChange({ lon: lng, lat })
            destMarkerRef.current?.setLngLat([lng, lat])
          }
        })
      })
      
      map.on('error', (e) => console.error('❌ Map error:', e))
    }, 100)

    return () => {
      clearTimeout(timer)
      if (mapRef.current) mapRef.current.remove()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Sync markers when coordinates change
  useEffect(() => {
    originMarkerRef.current?.setLngLat([origin.lon, origin.lat])
  }, [origin])

  useEffect(() => {
    destMarkerRef.current?.setLngLat([destination.lon, destination.lat])
  }, [destination])

  return (
    <div className="map-area">
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  )
})

Map.displayName = 'Map'
