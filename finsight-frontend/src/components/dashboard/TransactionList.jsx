// TransactionList — recent transactions with category icons + badges
import { getColor, getBg, getIcon } from '../../utils/categoryColors'
import { formatINR } from '../../utils/formatCurrency'
import { formatShortDate } from '../../utils/dateHelpers'
import Badge from '../ui/Badge'

function TxnRow({ txn }) {
  const isCredit = txn.type === 'credit'
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-blue-50 last:border-0">
      {/* Category icon */}
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: getBg(txn.category) }}
      >
        <i
          className={`ti ti-${getIcon(txn.category)} text-[14px]`}
          style={{ color: getColor(txn.category) }}
        />
      </div>

      {/* Description + category */}
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-medium text-slate-800 truncate">
          {txn.description}
          <Badge source={isCredit ? 'income' : txn.category_source} />
        </div>
        <div className="text-[11px] text-slate-400 mt-0.5">
          {txn.category} · {formatShortDate(txn.date)}
        </div>
      </div>

      {/* Amount */}
      <div className={`text-[13px] font-medium flex-shrink-0 ${isCredit ? 'text-emerald-600' : 'text-rose-500'}`}>
        {isCredit ? '+' : '-'}{formatINR(txn.amount)}
      </div>
    </div>
  )
}

export default function TransactionList({ transactions }) {
  // Show most recent 10 transactions
  const recent = (transactions ?? []).slice(0, 10)

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[13px] font-medium text-slate-800">Recent transactions</div>
        <span className="text-[11px] text-slate-400">{transactions?.length ?? 0} total</span>
      </div>

      <div>
        {recent.map((txn, i) => <TxnRow key={i} txn={txn} />)}
      </div>
    </div>
  )
}
