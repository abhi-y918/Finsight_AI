// App.jsx — routing setup
// ─────────────────────────────────────────────────────────────────
// React Router v6 manages which page to show based on the URL.
//
// Routes:
//   /           → Landing page
//   /upload     → Upload screen
//   /analyzing  → Analyzing progress screen
//   /dashboard  → Dashboard (requires result in route state)
// ─────────────────────────────────────────────────────────────────
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing   from './pages/Landing'
import Upload    from './pages/Upload'
import Analyzing from './pages/Analyzing'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"          element={<Landing />}   />
        <Route path="/upload"    element={<Upload />}    />
        <Route path="/analyzing" element={<Analyzing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        {/* Catch-all → redirect to home */}
        <Route path="*"          element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
