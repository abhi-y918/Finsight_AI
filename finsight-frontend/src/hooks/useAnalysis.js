// hooks/useAnalysis.js
// ─────────────────────────────────────────────────────────────────
// Custom hook that manages the full upload → analyze → result flow.
//
// STATES:
//   idle       → nothing happening
//   uploading  → file is being sent to backend
//   analyzing  → pipeline is running (show Analyzing screen)
//   complete   → result is ready (redirect to Dashboard)
//   error      → something went wrong
//
// USAGE in Upload.jsx:
//   const { upload, status, jobId, result, error } = useAnalysis()
//   <button onClick={() => upload(file)}>Analyze</button>
// ─────────────────────────────────────────────────────────────────
import { useState } from 'react'
import { analyzeStatement } from '../api/endpoints'

export const useAnalysis = () => {
  const [status, setStatus]   = useState('idle')      // idle | uploading | complete | error
  const [jobId,  setJobId]    = useState(null)
  const [result, setResult]   = useState(null)
  const [error,  setError]    = useState(null)

  const upload = async (file) => {
    try {
      setStatus('uploading')
      setError(null)

      // Phase 1 & 2: synchronous — result comes back immediately
      const data = await analyzeStatement(file)

      setJobId(data.job_id)
      setResult(data.result)
      setStatus('complete')

      // Phase 3 async upgrade:
      // setJobId(data.job_id)
      // setStatus('analyzing')   ← redirect to Analyzing screen, start polling

    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Upload failed. Please try again.'
      setError(msg)
      setStatus('error')
    }
  }

  const reset = () => {
    setStatus('idle')
    setJobId(null)
    setResult(null)
    setError(null)
  }

  return { upload, status, jobId, result, error, reset }
}