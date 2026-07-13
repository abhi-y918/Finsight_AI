export default function ExtractedMeta({ metadata }) {
  if (!metadata) return null
  
  return (
    <div className="bg-white border border-blue-100 rounded-xl p-4 mb-4 grid grid-cols-2 gap-4">
      <div>
        <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">Bank</div>
        <div className="text-sm font-medium text-slate-800 flex items-center gap-1.5">
          <i className="ti ti-building-bank text-blue-600" />
          {metadata.bank}
        </div>
      </div>
      <div>
        <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">Account</div>
        <div className="text-sm font-medium text-slate-800 flex items-center gap-1.5">
          <i className="ti ti-user text-blue-600" />
          {metadata.account_holder}
        </div>
      </div>
      <div className="col-span-2 pt-2 border-t border-blue-50">
        <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">Period</div>
        <div className="text-sm font-medium text-slate-800 flex items-center gap-1.5">
          <i className="ti ti-calendar text-blue-600" />
          {metadata.period_label} ({metadata.months} {metadata.months === 1 ? 'month' : 'months'})
        </div>
      </div>
    </div>
  )
}
