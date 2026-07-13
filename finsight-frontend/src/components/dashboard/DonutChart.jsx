// DonutChart — spending breakdown donut + legend
// Uses Recharts PieChart under the hood.
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { getColor } from '../../utils/categoryColors'
import { formatINR } from '../../utils/formatCurrency'

// Custom tooltip shown on hover
const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-white border border-blue-100 rounded-xl px-3 py-2 shadow-lg text-sm">
      <div className="font-medium text-slate-800">{d.category}</div>
      <div className="text-slate-500">{formatINR(d.amount)} · {d.percentage}%</div>
    </div>
  )
}

export default function DonutChart({ categories }) {
  if (!categories?.length) return null

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5">
      <div className="text-[13px] font-medium text-slate-800 mb-4">Spending breakdown</div>

      <div className="flex items-center gap-5">

        {/* Donut chart */}
        <div className="w-36 h-36 flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={categories}
                cx="50%" cy="50%"
                innerRadius={42}
                outerRadius={65}
                dataKey="amount"
                strokeWidth={2}
                stroke="#F0F5FF"
              >
                {categories.map((cat) => (
                  <Cell key={cat.category} fill={getColor(cat.category)} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex-1 flex flex-col gap-2.5">
          {categories.map((cat) => (
            <div key={cat.category} className="flex items-center gap-2 text-[12.5px]">
              <div
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ background: getColor(cat.category) }}
              />
              <span className="text-slate-500 flex-1">{cat.category}</span>
              <span className="font-medium text-slate-800 min-w-[32px] text-right">
                {cat.percentage}%
              </span>
              <span className="text-slate-400 text-[11px] min-w-[56px] text-right">
                {formatINR(cat.amount)}
              </span>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}
