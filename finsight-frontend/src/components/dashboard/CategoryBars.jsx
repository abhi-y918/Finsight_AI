import { getColor } from '../../utils/categoryColors'
import { formatINR } from '../../utils/formatCurrency'

export default function CategoryBars({ categories }) {
  if (!categories || categories.length === 0) return null

  // Don't show categories with 0 amount
  const validCats = categories.filter(c => c.amount > 0)
  
  // Find max percentage to scale bars relative to the biggest one
  const maxPct = Math.max(...validCats.map(c => c.percentage), 1)

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5 flex flex-col justify-center">
      <div className="text-[13px] font-medium text-slate-800 mb-4">Top spending categories</div>
      
      <div className="flex flex-col gap-4">
        {validCats.map(cat => {
          // Scale width so the largest bar is always 100% of the container width
          const relativeWidth = (cat.percentage / maxPct) * 100
          
          return (
            <div key={cat.category}>
              <div className="flex justify-between text-xs font-medium text-slate-700 mb-1.5">
                <span>{cat.category}</span>
                <span>{formatINR(cat.amount)}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-1000"
                  style={{ 
                    width: `${relativeWidth}%`,
                    backgroundColor: getColor(cat.category)
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
