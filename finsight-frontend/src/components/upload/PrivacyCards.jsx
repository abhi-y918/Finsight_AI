export default function PrivacyCards() {
  return (
    <div className="grid grid-cols-2 gap-4 mt-8">
      <div className="bg-white border border-blue-100 rounded-xl p-4 flex gap-3">
        <div className="w-8 h-8 bg-emerald-50 rounded-lg flex items-center justify-center flex-shrink-0">
          <i className="ti ti-shield-check text-emerald-600 text-lg" />
        </div>
        <div>
          <div className="text-sm font-medium text-slate-800 mb-0.5">Private by design</div>
          <div className="text-xs text-slate-500">Your data is processed in memory and never stored permanently.</div>
        </div>
      </div>
      <div className="bg-white border border-blue-100 rounded-xl p-4 flex gap-3">
        <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
          <i className="ti ti-lock text-blue-600 text-lg" />
        </div>
        <div>
          <div className="text-sm font-medium text-slate-800 mb-0.5">Bank-grade security</div>
          <div className="text-xs text-slate-500">No passwords or sensitive credentials are ever requested.</div>
        </div>
      </div>
    </div>
  )
}
