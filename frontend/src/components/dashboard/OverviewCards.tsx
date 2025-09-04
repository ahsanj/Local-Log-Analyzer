import { LogAnalysis, LogLevel } from '../../types'
import { formatNumber, formatDateTime } from '../../utils/formatters'
import { 
  DocumentTextIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon,
  ClockIcon 
} from '@heroicons/react/24/outline'

interface OverviewCardsProps {
  analysis: LogAnalysis
}

export default function OverviewCards({ analysis }: OverviewCardsProps) {
  const errorCount = (analysis.level_distribution[LogLevel.ERROR] || 0) + 
                     (analysis.level_distribution[LogLevel.FATAL] || 0) + 
                     (analysis.level_distribution[LogLevel.CRITICAL] || 0)
  
  const warningCount = (analysis.level_distribution[LogLevel.WARN] || 0) + 
                       (analysis.level_distribution[LogLevel.WARNING] || 0)
  
  const infoCount = analysis.level_distribution[LogLevel.INFO] || 0

  const cards = [
    {
      title: 'Total Entries',
      value: formatNumber(analysis.total_entries),
      icon: DocumentTextIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200'
    },
    {
      title: 'Errors',
      value: formatNumber(errorCount),
      icon: ExclamationTriangleIcon,
      color: 'text-error-600',
      bgColor: 'bg-error-50',
      borderColor: 'border-error-200'
    },
    {
      title: 'Warnings',
      value: formatNumber(warningCount),
      icon: ExclamationTriangleIcon,
      color: 'text-warning-600',
      bgColor: 'bg-warning-50',
      borderColor: 'border-warning-200'
    },
    {
      title: 'Info Messages',
      value: formatNumber(infoCount),
      icon: InformationCircleIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200'
    }
  ]

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {cards.map((card, index) => (
          <div 
            key={index}
            className={`card p-6 border ${card.borderColor}`}
          >
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${card.bgColor} mr-4`}>
                <card.icon className={`h-6 w-6 ${card.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                <p className="text-sm text-gray-600">{card.title}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Date Range */}
      {analysis.date_range.start && analysis.date_range.end && (
        <div className="card p-4 mb-6">
          <div className="flex items-center space-x-2 text-gray-600">
            <ClockIcon className="h-5 w-5" />
            <span className="text-sm">
              Time Range: {formatDateTime(analysis.date_range.start)} → {formatDateTime(analysis.date_range.end)}
            </span>
          </div>
        </div>
      )}

      {/* Services Summary */}
      {Object.keys(analysis.service_distribution).length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Services</h3>
          <div className="space-y-2">
            {Object.entries(analysis.service_distribution).slice(0, 5).map(([service, count]) => (
              <div key={service} className="flex items-center justify-between">
                <span className="text-sm text-gray-700 truncate">{service}</span>
                <span className="text-sm font-medium text-gray-900">{formatNumber(count)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}