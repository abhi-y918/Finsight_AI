export default function AgentSteps({ currentStep, completedSteps }) {
  const steps = [
    { id: 'ingestion', label: 'Extracting transactions' },
    { id: 'metadata', label: 'Reading statement details' },
    { id: 'categorization', label: 'AI categorizing spending' },
    { id: 'anomaly', label: 'Detecting unusual patterns' },
    { id: 'insight', label: 'Generating smart insights' },
    { id: 'aggregator', label: 'Finalizing report' }
  ]

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5 mb-4">
      <div className="flex flex-col gap-3">
        {steps.map((s, i) => {
          const isComplete = completedSteps.includes(s.id) || currentStep === 'complete'
          const isActive = currentStep === s.id && !isComplete
          const isPending = !isComplete && !isActive

          return (
            <div key={s.id} className={`flex items-center gap-3 text-sm ${isPending ? 'opacity-40' : ''}`}>
              <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0
                ${isComplete ? 'bg-emerald-100 text-emerald-600' : 
                  isActive ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-400'}`}
              >
                {isComplete ? (
                  <i className="ti ti-check text-xs font-bold" />
                ) : isActive ? (
                  <i className="ti ti-loader animate-spin text-xs" />
                ) : (
                  <span className="text-[10px] font-medium">{i + 1}</span>
                )}
              </div>
              <span className={`font-medium ${isActive ? 'text-blue-700' : 'text-slate-600'}`}>
                {s.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
