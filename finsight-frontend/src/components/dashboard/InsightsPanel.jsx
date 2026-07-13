// InsightsPanel — AI-generated financial insights
import { getColor, getBg, getIcon } from '../../utils/categoryColors'

const TYPE_CONFIG = {
  warning: { icon: 'alert-triangle', bg: '#FFE4E6', color: '#E11D48' },
  tip:     { icon: 'bulb',           bg: '#D1FAE5', color: '#0D9373' },
  info:    { icon: 'info-circle',    bg: '#DBEAFE', color: '#2563EB' },
}

function InsightCard({ insight }) {
  const cfg = TYPE_CONFIG[insight.type] ?? TYPE_CONFIG.info
  const catBg    = insight.category ? getBg(insight.category)    : cfg.bg
  const catColor = insight.category ? getColor(insight.category) : cfg.color
  const catIcon  = insight.category ? getIcon(insight.category)  : cfg.icon

  return (
    <div className="bg-blue-50 rounded-lg p-3 flex gap-3">
      <div
        className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
        style={{ background: catBg }}
      >
        <i className={`ti ti-${catIcon} text-[13px]`} style={{ color: catColor }} />
      </div>
      <div>
        <div className="text-[12.5px] font-medium text-slate-800 mb-0.5">{insight.title}</div>
        <div className="text-[11.5px] text-slate-500 leading-relaxed">{insight.description}</div>
      </div>
    </div>
  )
}

export default function InsightsPanel({ insights, anomalies }) {
  // Merge insights + high-severity anomalies
  const items = [
    ...(insights ?? []),
    ...(anomalies ?? [])
      .filter(a => a.severity === 'high')
      .map(a => ({ title: a.title, description: a.description, type: 'warning', category: a.category }))
  ].slice(0, 5)

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="text-[13px] font-medium text-slate-800">AI insights</div>
        <span className="text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded-full font-medium">
          {items.length}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {items.length > 0
          ? items.map((ins, i) => <InsightCard key={i} insight={ins} />)
          : <div className="text-[12.5px] text-slate-400 text-center py-4">No insights yet</div>
        }
      </div>
    </div>
  )
}
