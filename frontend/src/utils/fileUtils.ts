import { LogFormat } from '../types'

export const SUPPORTED_EXTENSIONS = ['.log', '.txt', '.csv', '.syslog', '.json'] as const
export const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
export const MAX_PASTE_SIZE = 10 * 1024 * 1024 // 10MB for paste content

export interface FileValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

export interface FileInfo {
  name: string
  size: number
  type: string
  extension: string
  format: LogFormat
  lastModified: Date
  preview?: string
}

export function validateFile(file: File): FileValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`File size (${formatFileSize(file.size)}) exceeds maximum limit of ${formatFileSize(MAX_FILE_SIZE)}`)
  }

  // Check file extension
  const extension = getFileExtension(file.name).toLowerCase()
  if (!SUPPORTED_EXTENSIONS.includes(extension as any)) {
    errors.push(`File type "${extension}" is not supported. Supported types: ${SUPPORTED_EXTENSIONS.join(', ')}`)
  }

  // Check if file is empty
  if (file.size === 0) {
    errors.push('File is empty')
  }

  // Warnings for large files
  if (file.size > 25 * 1024 * 1024) { // 25MB
    warnings.push('Large file detected. Processing may take longer than usual.')
  }

  // Check file name
  if (file.name.length > 255) {
    warnings.push('File name is very long and may be truncated')
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

export function validatePasteContent(content: string): FileValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  const contentSize = new Blob([content]).size

  // Check content size
  if (contentSize > MAX_PASTE_SIZE) {
    errors.push(`Content size (${formatFileSize(contentSize)}) exceeds maximum limit of ${formatFileSize(MAX_PASTE_SIZE)} for pasted content`)
  }

  // Check if content is empty
  if (content.trim().length === 0) {
    errors.push('Pasted content is empty')
  }

  // Check for very long lines (potential issues)
  const lines = content.split('\n')
  const maxLineLength = Math.max(...lines.map(line => line.length))
  if (maxLineLength > 10000) {
    warnings.push('Some lines are extremely long. This may affect processing performance.')
  }

  // Check line count
  if (lines.length > 100000) {
    warnings.push('Content has many lines. Processing may take longer than usual.')
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

export function getFileExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? `.${parts.pop()!.toLowerCase()}` : ''
}

export function detectLogFormat(filename: string, content?: string): LogFormat {
  const extension = getFileExtension(filename).toLowerCase()
  
  // First, check by extension
  switch (extension) {
    case '.json':
      return LogFormat.JSON
    case '.csv':
      return LogFormat.CSV
    case '.syslog':
      return LogFormat.SYSLOG
    case '.log':
    case '.txt':
    default:
      // If we have content, try to detect format
      if (content) {
        return detectFormatFromContent(content)
      }
      return LogFormat.PLAIN_TEXT
  }
}

function detectFormatFromContent(content: string): LogFormat {
  const sample = content.substring(0, 2000) // First 2KB for detection
  const lines = sample.split('\n').filter(line => line.trim().length > 0)
  
  if (lines.length === 0) return LogFormat.PLAIN_TEXT

  // JSON detection
  let jsonCount = 0
  for (const line of lines.slice(0, 5)) {
    try {
      JSON.parse(line.trim())
      jsonCount++
    } catch {
      // Not JSON
    }
  }
  if (jsonCount >= Math.min(3, lines.length)) {
    return LogFormat.JSON
  }

  // CSV detection
  const firstLine = lines[0]
  const secondLine = lines[1]
  if (firstLine && secondLine) {
    const firstCommas = (firstLine.match(/,/g) || []).length
    const secondCommas = (secondLine.match(/,/g) || []).length
    if (firstCommas > 2 && Math.abs(firstCommas - secondCommas) <= 1) {
      return LogFormat.CSV
    }
  }

  // Syslog detection patterns
  const syslogPatterns = [
    /^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}/, // Jan 01 12:00:00
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/, // ISO timestamp
    /^<\d+>/ // Priority
  ]
  
  let syslogMatches = 0
  for (const line of lines.slice(0, 5)) {
    for (const pattern of syslogPatterns) {
      if (pattern.test(line)) {
        syslogMatches++
        break
      }
    }
  }
  if (syslogMatches >= Math.min(2, lines.length)) {
    return LogFormat.SYSLOG
  }

  return LogFormat.PLAIN_TEXT
}

export async function getFileInfo(file: File): Promise<FileInfo> {
  const extension = getFileExtension(file.name)
  const format = detectLogFormat(file.name)
  
  // Get file preview
  let preview: string | undefined
  try {
    if (file.size <= 1024 * 1024) { // Only preview files <= 1MB
      const text = await file.text()
      preview = text.substring(0, 500) // First 500 chars
    }
  } catch (error) {
    // Preview not available
  }

  return {
    name: file.name,
    size: file.size,
    type: file.type,
    extension,
    format,
    lastModified: new Date(file.lastModified),
    preview
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function getFormatDescription(format: LogFormat): string {
  switch (format) {
    case LogFormat.JSON:
      return 'Structured JSON logs with one JSON object per line'
    case LogFormat.CSV:
      return 'Comma-separated values with headers'
    case LogFormat.SYSLOG:
      return 'Standard system log format with timestamps and priorities'
    case LogFormat.PLAIN_TEXT:
      return 'Plain text log entries, one per line'
    default:
      return 'Custom or unknown log format'
  }
}

export function getFormatIcon(format: LogFormat): string {
  switch (format) {
    case LogFormat.JSON:
      return '{ }'
    case LogFormat.CSV:
      return '📊'
    case LogFormat.SYSLOG:
      return '🖥️'
    case LogFormat.PLAIN_TEXT:
      return '📄'
    default:
      return '❓'
  }
}

export function isTextFile(file: File): boolean {
  const textTypes = [
    'text/',
    'application/json',
    'application/csv',
    'application/x-csv',
    'text/csv'
  ]
  
  return textTypes.some(type => file.type.startsWith(type)) || 
         SUPPORTED_EXTENSIONS.includes(getFileExtension(file.name) as any)
}

export function generatePreviewLines(content: string, maxLines: number = 10): string[] {
  return content
    .split('\n')
    .slice(0, maxLines)
    .map(line => line.length > 100 ? line.substring(0, 100) + '...' : line)
}