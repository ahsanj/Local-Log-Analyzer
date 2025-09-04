import { PatternMatch } from '../../types'
import { formatDateTime } from '../../utils/formatters'
import { ExclamationTriangleIcon, InformationCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface PatternsListProps {
  patterns: PatternMatch[]
}

export default function PatternsList({ patterns }: PatternsListProps) {
  if (!patterns || patterns.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Error Patterns</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>No patterns detected</p>
        </div>
      </div>
    )
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-error-600" />
      case 'medium':
        return <ExclamationCircleIcon className="h-5 w-5 text-warning-600" />
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-600" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-error-50 text-error-700 border-error-200'
      case 'medium':
        return 'bg-warning-50 text-warning-700 border-warning-200'
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200'
    }
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Error Patterns</h3>
      <div className="space-y-4 max-h-80 overflow-y-auto">
        {patterns.slice(0, 10).map((pattern, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                {getSeverityIcon(pattern.severity)}
                <h4 className="text-sm font-medium text-gray-900">
                  {pattern.pattern}
                </h4>
              </div>
              <div className="flex items-center space-x-2">
                <span className={clsx(
                  'px-2 py-1 text-xs font-medium rounded-full border',
                  getSeverityColor(pattern.severity)
                )}>
                  {pattern.severity}
                </span>
                <span className="text-sm font-medium text-gray-900">
                  {pattern.count}x
                </span>
              </div>
            </div>
            
            {pattern.examples && pattern.examples.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-gray-600 mb-1">Example:</p>
                <p className="text-xs text-gray-800 bg-gray-50 p-2 rounded font-mono">
                  {pattern.examples[0].length > 100 
                    ? pattern.examples[0].substring(0, 100) + '...'
                    : pattern.examples[0]
                  }
                </p>
              </div>
            )}
            
            {(pattern.first_occurrence || pattern.last_occurrence) && (
              <div className="text-xs text-gray-500">
                {pattern.first_occurrence && pattern.last_occurrence ? (
                  <span>
                    First: {formatDateTime(pattern.first_occurrence)} • 
                    Last: {formatDateTime(pattern.last_occurrence)}
                  </span>
                ) : pattern.first_occurrence ? (
                  <span>Occurred: {formatDateTime(pattern.first_occurrence)}</span>
                ) : pattern.last_occurrence ? (
                  <span>Last: {formatDateTime(pattern.last_occurrence)}</span>
                ) : null}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {patterns.length > 10 && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-500">
            Showing top 10 patterns out of {patterns.length} detected
          </p>
        </div>
      )}
    </div>
  )
}