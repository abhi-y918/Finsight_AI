export default function AlertBanner({ anomalies }) {
  if (!anomalies || anomalies.length === 0) return null

  // Show only the top highest severity anomaly here if it's 'high' severity
  const topAnomaly = anomalies.find(a => a.severity === 'high')
  if (!topAnomaly) return null

  return (
    <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 mb-5 flex items-start gap-3">
      <div className="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
        <i className="ti ti-alert-triangle text-rose-600 text-lg" />
      </div>
      <div>
        <div className="text-sm font-semibold text-rose-800 mb-0.5">Attention needed: {topAnomaly.title}</div>
        <div className="text-sm text-rose-700 leading-relaxed">{topAnomaly.description}</div>
      </div>
    </div>
  )
}
