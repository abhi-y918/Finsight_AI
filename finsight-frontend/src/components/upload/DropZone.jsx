import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function DropZone({ onFile, loading }) {
  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles?.length > 0) {
      onFile(acceptedFiles[0])
    }
  }, [onFile])
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv']
    },
    maxFiles: 1,
    disabled: loading
  })

  return (
    <div 
      {...getRootProps()} 
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-blue-200 bg-white hover:border-blue-400 hover:bg-slate-50'}
        ${loading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
        {loading ? (
          <i className="ti ti-loader animate-spin text-blue-600 text-xl" />
        ) : (
          <i className="ti ti-upload text-blue-600 text-xl" />
        )}
      </div>
      <div className="text-sm font-medium text-slate-800 mb-1">
        {loading ? 'Analyzing statement...' : 'Click or drag PDF/CSV here'}
      </div>
      <div className="text-xs text-slate-400">
        Up to 10MB
      </div>
    </div>
  )
}
