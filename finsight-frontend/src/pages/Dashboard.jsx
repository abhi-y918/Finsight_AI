// pages/Dashboard.jsx — the main dashboard screen
import { useLocation, useNavigate } from 'react-router-dom'
import Topbar          from '../components/layout/Topbar'
import MetricCards     from '../components/dashboard/MetricCards'
import AlertBanner     from '../components/dashboard/AlertBanner'
import DonutChart      from '../components/dashboard/DonutChart'
import CategoryBars    from '../components/dashboard/CategoryBars'
import TransactionList from '../components/dashboard/TransactionList'
import InsightsPanel   from '../components/dashboard/InsightsPanel'

export default function Dashboard() {
  const { state } = useLocation()
  const navigate  = useNavigate()

  // Result comes from Upload via react-router state
  const result = state?.result

  // If no result (e.g. direct URL access), redirect to upload
  if (!result) {
    navigate('/upload')
    return null
  }

  const { metadata, summary, categories, transactions, anomalies, insights } = result

  return (
    <div className="min-h-screen bg-[#F0F5FF] p-5">

      {/* Topbar */}
      <Topbar
        metadata={metadata}
        onReupload={() => navigate('/upload')}
      />

      {/* Metric cards */}
      <MetricCards summary={summary} metadata={metadata} />

      {/* Alert banner — top anomaly */}
      <AlertBanner anomalies={anomalies} />

      {/* Row 1: Donut + Bars */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <DonutChart   categories={categories} />
        <CategoryBars categories={categories} />
      </div>

      {/* Row 2: Transactions + Insights */}
      <div className="grid grid-cols-2 gap-4">
        <TransactionList transactions={transactions} />
        <InsightsPanel   insights={insights} anomalies={anomalies} />
      </div>

    </div>
  )
}
