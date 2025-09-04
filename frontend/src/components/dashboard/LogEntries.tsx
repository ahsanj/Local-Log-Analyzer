import { useState, useEffect } from 'react'
import { analysisApi } from '../../services/api'
import { LogEntry } from '../../types'
import { getLogLevelColor, formatDateTime, truncateString } from '../../utils/formatters'
import { ChevronLeftIcon, ChevronRightIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface LogEntriesProps {
  fileId: string
}

export default function LogEntries({ fileId }: LogEntriesProps) {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [totalEntries, setTotalEntries] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [filters, setFilters] = useState({
    level: '',
    service: '',
    search: ''
  })
  
  const entriesPerPage = 50

  useEffect(() => {
    loadEntries()
  }, [fileId, currentPage, filters])

  const loadEntries = async () => {
    setIsLoading(true)
    try {
      const offset = (currentPage - 1) * entriesPerPage
      const response = await analysisApi.getEntries(fileId, {
        offset,
        limit: entriesPerPage,
        level: filters.level || undefined,
        service: filters.service || undefined,
        search: filters.search || undefined
      })
      
      setEntries(response.entries)
      setTotalEntries(response.total)
    } catch (error) {
      console.error('Failed to load entries:', error)
      setEntries([])
      setTotalEntries(0)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setCurrentPage(1) // Reset to first page when filtering
  }

  const clearFilters = () => {
    setFilters({ level: '', service: '', search: '' })
    setCurrentPage(1)
  }

  const totalPages = Math.ceil(totalEntries / entriesPerPage)
  const startIndex = (currentPage - 1) * entriesPerPage + 1
  const endIndex = Math.min(currentPage * entriesPerPage, totalEntries)

  return (
    <div className="flex flex-col h-full">
      {/* Filters */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex flex-wrap items-center space-x-4 space-y-2">
          {/* Search */}
          <div className="flex-1 min-w-64">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search log messages..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="pl-10 w-full input-field"
              />
            </div>
          </div>
          
          {/* Level Filter */}
          <select
            value={filters.level}
            onChange={(e) => handleFilterChange('level', e.target.value)}
            className="input-field w-32"
          >
            <option value="">All Levels</option>
            <option value="ERROR">Error</option>
            <option value="WARN">Warning</option>
            <option value="INFO">Info</option>
            <option value="DEBUG">Debug</option>
          </select>
          
          {/* Service Filter */}
          <input
            type="text"
            placeholder="Service name"
            value={filters.service}
            onChange={(e) => handleFilterChange('service', e.target.value)}
            className="input-field w-40"
          />
          
          {/* Clear Filters */}
          {(filters.level || filters.service || filters.search) && (
            <button
              onClick={clearFilters}
              className="btn-secondary text-sm"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Entries List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading entries...</p>
            </div>
          </div>
        ) : entries.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-500">
              <p>No log entries found</p>
              {(filters.level || filters.service || filters.search) && (
                <p className="text-sm mt-1">Try adjusting your filters</p>
              )}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {entries.map((entry, index) => (
              <div key={index} className="p-4 hover:bg-gray-50">
                <div className="flex items-start space-x-3">
                  {/* Line Number */}
                  <span className="text-xs text-gray-400 font-mono w-16 text-right flex-shrink-0 mt-1">
                    {entry.line_number}
                  </span>
                  
                  {/* Timestamp */}
                  <span className="text-xs text-gray-500 w-40 flex-shrink-0 mt-1">
                    {entry.timestamp ? formatDateTime(entry.timestamp) : '-'}
                  </span>
                  
                  {/* Level Badge */}
                  {entry.level && (
                    <span className={clsx(
                      'px-2 py-1 text-xs font-medium rounded border flex-shrink-0',
                      getLogLevelColor(entry.level)
                    )}>
                      {entry.level}
                    </span>
                  )}
                  
                  {/* Service */}
                  {entry.service && (
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded flex-shrink-0">
                      {truncateString(entry.service, 20)}
                    </span>
                  )}
                  
                  {/* Message */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 font-mono whitespace-pre-wrap break-words">
                      {entry.message}
                    </p>
                    {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          Metadata
                        </summary>
                        <pre className="text-xs text-gray-600 mt-1 bg-gray-50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(entry.metadata, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white border-t border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{startIndex}</span> to{' '}
                  <span className="font-medium">{endIndex}</span> of{' '}
                  <span className="font-medium">{totalEntries.toLocaleString()}</span> results
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeftIcon className="h-5 w-5" />
                </button>
                
                <div className="flex space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum
                    if (totalPages <= 5) {
                      pageNum = i + 1
                    } else if (currentPage <= 3) {
                      pageNum = i + 1
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i
                    } else {
                      pageNum = currentPage - 2 + i
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={clsx(
                          'px-3 py-2 text-sm font-medium rounded',
                          pageNum === currentPage
                            ? 'bg-primary-600 text-white'
                            : 'text-gray-700 hover:bg-gray-100'
                        )}
                      >
                        {pageNum}
                      </button>
                    )
                  })}
                </div>
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRightIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}