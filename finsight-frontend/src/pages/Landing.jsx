// pages/Landing.jsx — hero, features, how-it-works
import { useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'

const FEATURES = [
  { icon: 'brain',          bg: '#DBEAFE', color: '#2563EB', title: 'AI categorization',    desc: 'Even raw UPI names like "ANI Technologies" get mapped to the right category automatically.' },
  { icon: 'shield-check',   bg: '#D1FAE5', color: '#0D9373', title: 'Private & secure',     desc: 'Your statement is processed and never stored. No data leaves your session.' },
  { icon: 'building-bank',  bg: '#EDE9FE', color: '#7C3AED', title: 'All banks supported',  desc: 'HDFC, SBI, ICICI, Axis, Kotak and more — PDF or CSV, we handle it all.' },
]

const HOW = [
  { n: '1', title: 'Upload statement',  desc: 'Drop your bank PDF or CSV. We support all major Indian banks.' },
  { n: '2', title: 'AI analyzes it',    desc: 'Our agent extracts transactions, categorizes spending, and detects patterns.' },
  { n: '3', title: 'See your dashboard',desc: 'Get a full breakdown with insights, anomalies, and savings tips.' },
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#F0F5FF] p-5">

      {/* Navbar */}
      <div className="flex items-center justify-between mb-10 max-w-4xl mx-auto">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <i className="ti ti-chart-pie text-white text-[17px]" />
          </div>
          <span className="text-[15px] font-medium text-slate-800">FinSight AI</span>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">Log in</Button>
          <Button variant="primary" onClick={() => navigate('/upload')}>Get started</Button>
        </div>
      </div>

      {/* Hero */}
      <div className="text-center py-10 max-w-2xl mx-auto">
        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <i className="ti ti-sparkles text-white text-3xl" />
        </div>
        <h1 className="text-3xl font-medium text-slate-800 mb-3 leading-snug">
          Understand your money<br />in seconds
        </h1>
        <p className="text-[14px] text-slate-500 max-w-md mx-auto mb-7 leading-relaxed">
          Upload any bank statement and our AI agent automatically extracts,
          categorizes, and analyzes every transaction — no manual entry ever.
        </p>
        <div className="flex gap-3 justify-center">
          <Button variant="primary" icon="upload" onClick={() => navigate('/upload')}>
            Upload your statement
          </Button>
          <Button variant="outline">See a demo</Button>
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-3 gap-4 max-w-4xl mx-auto mb-6">
        {FEATURES.map(f => (
          <div key={f.title} className="bg-white border border-blue-100 rounded-xl p-5 text-center">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-3"
              style={{ background: f.bg }}>
              <i className={`ti ti-${f.icon} text-lg`} style={{ color: f.color }} />
            </div>
            <div className="text-[13px] font-medium text-slate-800 mb-1.5">{f.title}</div>
            <div className="text-[12px] text-slate-400 leading-relaxed">{f.desc}</div>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div className="grid grid-cols-3 gap-4 max-w-4xl mx-auto">
        {HOW.map(h => (
          <div key={h.title} className="bg-white border border-blue-100 rounded-xl p-4 flex gap-3">
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center text-white text-[12px] font-medium flex-shrink-0">
              {h.n}
            </div>
            <div>
              <div className="text-[13px] font-medium text-slate-800 mb-1">{h.title}</div>
              <div className="text-[12px] text-slate-400 leading-relaxed">{h.desc}</div>
            </div>
          </div>
        ))}
      </div>

    </div>
  )
}
