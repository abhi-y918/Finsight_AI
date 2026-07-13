export default function Button({ children, variant = 'primary', icon, onClick, disabled }) {
  const base = "inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors"
  
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300",
    outline: "border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
  }

  return (
    <button 
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]}`}
    >
      {icon && <i className={`ti ti-${icon} text-lg`} />}
      {children}
    </button>
  )
}
