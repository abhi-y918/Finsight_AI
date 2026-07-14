import { formatINR } from '../../utils/formatCurrency'

export default function MetricCards({ summary, metadata }) {
  if (!summary) return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <i className="ti ti-wallet text-indigo-500" />
          <span className="text-xs font-medium uppercase tracking-wide">Opening Balance</span>
        </div>
        <div className="text-2xl font-semibold text-slate-800">{formatINR(summary.opening_balance || 0)}</div>
      </div>

      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <i className="ti ti-arrow-down-right text-emerald-500" />
          <span className="text-xs font-medium uppercase tracking-wide">Total Income</span>
        </div>
        <div className="text-2xl font-semibold text-slate-800">{formatINR(summary.total_income)}</div>
      </div>

      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <i className="ti ti-arrow-up-right text-rose-500" />
          <span className="text-xs font-medium uppercase tracking-wide">Total Spent</span>
        </div>
        <div className="text-2xl font-semibold text-slate-800">{formatINR(summary.total_spending)}</div>
      </div>

      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <i className="ti ti-pig-money text-blue-500" />
          <span className="text-xs font-medium uppercase tracking-wide">Net Savings</span>
        </div>
        <div className="text-2xl font-semibold text-slate-800">{formatINR(summary.net)}</div>
        <div className="text-xs font-medium text-emerald-600 mt-1">
          {summary.savings_rate}% savings rate
        </div>
      </div>

      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <i className="ti ti-building-bank text-amber-500" />
          <span className="text-xs font-medium uppercase tracking-wide">Closing Balance</span>
        </div>
        <div className="text-2xl font-semibold text-slate-800">{formatINR(summary.closing_balance || 0)}</div>
      </div>

      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <i className="ti ti-brain text-purple-500" />
          <span className="text-xs font-medium uppercase tracking-wide">AI Confidence</span>
        </div>
        <div className="text-2xl font-semibold text-slate-800">{metadata.categorized_pct}%</div>
        <div className="text-xs font-medium text-slate-400 mt-1">
          Categorized automatically
        </div>
      </div>
    </div>
  )
}
