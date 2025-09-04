import { formatDistanceToNow as fnsFormatDistanceToNow, parseISO, format } from 'date-fns'

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function formatDistanceToNow(dateString: string): string {
  try {
    const date = parseISO(dateString)
    return fnsFormatDistanceToNow(date, { addSuffix: true })
  } catch {
    return 'Unknown time'
  }
}

export function formatDateTime(dateString: string): string {
  try {
    const date = parseISO(dateString)
    return format(date, 'MMM dd, yyyy HH:mm:ss')
  } catch {
    return 'Invalid date'
  }
}

export function formatNumber(num: number): string {
  return num.toLocaleString()
}

export function formatPercentage(value: number, total: number): string {
  if (total === 0) return '0%'
  return `${((value / total) * 100).toFixed(1)}%`
}

export function truncateString(str: string, length: number = 100): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function getLogLevelColor(level: string): string {
  switch (level?.toUpperCase()) {
    case 'ERROR':
    case 'FATAL':
    case 'CRITICAL':
      return 'text-error-600 bg-error-50 border-error-200'
    case 'WARN':
    case 'WARNING':
      return 'text-warning-600 bg-warning-50 border-warning-200'
    case 'INFO':
      return 'text-blue-600 bg-blue-50 border-blue-200'
    case 'DEBUG':
    case 'TRACE':
      return 'text-gray-600 bg-gray-50 border-gray-200'
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}