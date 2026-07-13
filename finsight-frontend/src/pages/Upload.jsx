// pages/Upload.jsx — file upload screen
import { useNavigate } from 'react-router-dom'
import { useAnalysis } from '../hooks/useAnalysis'
import DropZone from '../components/upload/DropZone'
import PrivacyCards from '../components/upload/PrivacyCards'

const BANKS = ['HDFC Bank', 'SBI', 'ICICI Bank', 'Axis Bank', 'Kotak', '+ more']

export default function Upload() {
  const navigate  = useNavigate()
  const { upload, status, result, error } = useAnalysis()

  const handleFile = async (file) => {
    const data = await upload(file)
    // After upload completes, go straight to dashboard with result
    // (Phase 1 & 2 are synchronous — no polling needed yet)
  }

  // When result is ready, redirect to dashboard
  if (status === 'complete' && result) {
    navigate('/dashboard', { state: { result } })
  }

  const loading = status === 'uploading'

  return (
    <div className="min-h-screen bg-[#F0F5FF] p-5 flex flex-col items-center justify-center">

      {/* Header */}
      <div className="flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <i className="ti ti-chart-pie text-white text-[17px]" />
        </div>
        <span className="text-[15px] font-medium text-slate-800">FinSight AI</span>
      </div>

      <div className="w-full max-w-lg">

        {/* Title */}
        <div className="text-center mb-6">
          <div className="text-xl font-medium text-slate-800 mb-1.5">Upload your bank statement</div>
          <div className="text-[13px] text-slate-400">
            We'll extract everything automatically — bank, name, period, and all transactions
          </div>
        </div>

        {/* Drop zone */}
        <DropZone onFile={handleFile} loading={loading} />

        {/* Error */}
        {error && (
          <div className="mt-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-[13px] text-red-600 flex items-center gap-2">
            <i className="ti ti-alert-circle" />
            {error}
          </div>
        )}

        {/* Supported banks */}
        <div className="text-center mt-5 mb-2 text-[12px] text-slate-400">Supported banks</div>
        <div className="flex flex-wrap gap-2 justify-center mb-4">
          {BANKS.map(b => (
            <span key={b} className="text-[11.5px] bg-blue-50 text-blue-600 border border-blue-200 px-2.5 py-1 rounded-full">
              {b}
            </span>
          ))}
        </div>

        {/* Privacy cards */}
        <PrivacyCards />

      </div>
    </div>
  )
}
