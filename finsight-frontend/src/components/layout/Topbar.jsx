// components/layout/Topbar.jsx
// The top navigation bar — shows logo, extracted metadata, re-upload button.
// Shows different content before/after upload.

import Button from '../ui/Button'

export default function Topbar({ metadata, onReupload }) {
  return (
    <div className="flex items-center justify-between mb-5">

      {/* Left: Logo + metadata */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <i className="ti ti-chart-pie text-white text-[17px]" />
        </div>
        <div>
          <div className="text-[15px] font-medium text-slate-800">FinSight AI</div>
          {metadata ? (
            <div className="flex items-center gap-1.5 text-[11.5px] text-slate-400 mt-0.5">
              <i className="ti ti-building-bank text-[11px]" />
              <span>{metadata.bank}</span>
              <span className="w-1 h-1 rounded-full bg-slate-300 inline-block" />
              <span>{metadata.account_holder}</span>
              <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-px rounded-full font-medium ml-1">
                from statement
              </span>
            </div>
          ) : (
            <div className="text-[11.5px] text-slate-400 mt-0.5">
              AI-powered bank statement analyzer
            </div>
          )}
        </div>
      </div>

      {/* Right: Period pill + action button */}
      <div className="flex items-center gap-2">
        {metadata && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-blue-200 rounded-lg text-[12.5px] text-blue-600 font-medium">
            <i className="ti ti-calendar text-[13px]" />
            {metadata.period_label}
            <span className="w-px h-3.5 bg-blue-200 mx-1" />
            <span className="text-slate-400 font-normal text-[11.5px]">
              {metadata.months} {metadata.months === 1 ? 'month' : 'months'}
            </span>
          </div>
        )}
        {onReupload && (
          <Button variant="outline" icon="refresh" onClick={onReupload}>
            Re-upload
          </Button>
        )}
      </div>

    </div>
  )
}
