// pages/Analyzing.jsx — live agent progress screen
// Used in Phase 3+ when pipeline becomes async.
// For now it shows a simulated progress while the sync call completes.
import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import AgentSteps from '../components/analyzing/AgentSteps'
import ExtractedMeta from '../components/analyzing/ExtractedMeta'

// Simulate step progression for sync pipeline (Phase 1 & 2)
// In Phase 3 async this will use real usePolling hook
const SIMULATED_STEPS = ['ingestion', 'metadata', 'categorization', 'anomaly', 'insight', 'aggregator']

export default function Analyzing() {
  const { state }  = useLocation()
  const navigate   = useNavigate()
  const { file, result } = state ?? {}

  const [stepIdx, setStepIdx]         = useState(0)
  const [completedSteps, setCompleted] = useState([])
  const [progressPct, setProgress]    = useState(5)

  useEffect(() => {
    // If result already available (sync), fast-forward through steps
    if (result) {
      let i = 0
      const interval = setInterval(() => {
        if (i < SIMULATED_STEPS.length) {
          setCompleted(prev => [...prev, SIMULATED_STEPS[i]])
          setStepIdx(i + 1)
          setProgress(Math.round(((i + 1) / SIMULATED_STEPS.length) * 100))
          i++
        } else {
          clearInterval(interval)
          setTimeout(() => navigate('/dashboard', { state: { result } }), 600)
        }
      }, 400)
      return () => clearInterval(interval)
    }
  }, [result])

  const currentStep = SIMULATED_STEPS[stepIdx] ?? 'complete'
  const meta = result?.metadata

  return (
    <div className="min-h-screen bg-[#F0F5FF] p-5 flex flex-col items-center justify-center">

      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="text-lg font-medium text-slate-800 mb-1">Analyzing your statement</div>
          <div className="text-[13px] text-slate-400">Our AI agent is reading and categorizing your transactions</div>
        </div>

        {/* File card */}
        <div className="bg-white border border-blue-100 rounded-xl px-4 py-3 flex items-center gap-3 mb-4">
          <div className="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <i className="ti ti-file-type-pdf text-blue-600 text-lg" />
          </div>
          <div className="flex-1">
            <div className="text-[13px] font-medium text-slate-800">{file?.name ?? 'statement.pdf'}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {file ? `${(file.size / 1024).toFixed(0)} KB` : ''} · Uploaded
            </div>
          </div>
          <i className="ti ti-check text-emerald-500 text-[18px]" />
        </div>

        {/* Extracted metadata */}
        {meta && <ExtractedMeta metadata={meta} />}

        {/* Agent steps */}
        <AgentSteps currentStep={currentStep} completedSteps={completedSteps} />

        {/* Progress bar */}
        <div className="mt-4">
          <div className="h-1.5 bg-blue-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <div className="text-[12px] text-slate-400 text-center mt-2">
            {progressPct}% complete
          </div>
        </div>

      </div>
    </div>
  )
}
