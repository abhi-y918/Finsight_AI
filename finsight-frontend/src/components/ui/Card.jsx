export default function Card({ children, className = '' }) {
  return (
    <div className={`bg-white border border-blue-100 rounded-xl shadow-sm ${className}`}>
      {children}
    </div>
  )
}
