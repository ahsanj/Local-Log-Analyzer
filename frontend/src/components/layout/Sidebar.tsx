import { useNavigate, useLocation } from 'react-router-dom'
import { 
  DocumentArrowUpIcon, 
  ChartBarIcon, 
  TrashIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { useFileStore } from '../../hooks/useFileStore'
import { formatFileSize, formatDistanceToNow } from '../../utils/formatters'
import clsx from 'clsx'

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { files, deleteFile } = useFileStore()

  const handleFileSelect = (fileId: string) => {
    navigate(`/dashboard/${fileId}`)
  }

  const handleFileDelete = async (e: React.MouseEvent, fileId: string) => {
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this file?')) {
      await deleteFile(fileId)
    }
  }

  const isFileSelected = (fileId: string) => {
    return location.pathname.includes(fileId)
  }

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={() => navigate('/')}
          className="w-full btn-primary flex items-center justify-center space-x-2"
        >
          <DocumentArrowUpIcon className="h-5 w-5" />
          <span>Upload New File</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
            Uploaded Files ({files.length})
          </h2>
          
          {files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <ChartBarIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No files uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className={clsx(
                    'p-3 rounded-lg border cursor-pointer transition-all duration-200',
                    isFileSelected(file.id)
                      ? 'bg-primary-50 border-primary-200 ring-1 ring-primary-200'
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  )}
                  onClick={() => handleFileSelect(file.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.filename}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs text-gray-500">
                          {formatFileSize(file.size)}
                        </span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className={clsx(
                          'text-xs px-2 py-1 rounded-full',
                          {
                            'bg-blue-100 text-blue-800': file.format === 'json',
                            'bg-green-100 text-green-800': file.format === 'csv',
                            'bg-yellow-100 text-yellow-800': file.format === 'syslog',
                            'bg-gray-100 text-gray-800': file.format === 'plain_text',
                            'bg-purple-100 text-purple-800': file.format === 'custom',
                          }
                        )}>
                          {file.format.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1 mt-2">
                        <ClockIcon className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {formatDistanceToNow(file.upload_time)}
                        </span>
                      </div>
                      {file.analysis && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-600">
                            {file.analysis.total_entries.toLocaleString()} entries
                          </p>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={(e) => handleFileDelete(e, file.id)}
                      className="ml-2 p-1 text-gray-400 hover:text-error-600 transition-colors"
                      title="Delete file"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 space-y-1">
          <p>🔒 All processing happens locally</p>
          <p>📊 Max file size: 50MB</p>
          <p>🤖 Powered by CodeLlama 13B</p>
        </div>
      </div>
    </div>
  )
}