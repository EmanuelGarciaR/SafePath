import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// Temporarily comment out to test if this is blocking
// import 'maplibre-gl/dist/maplibre-gl.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
