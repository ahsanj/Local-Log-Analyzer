export interface LogFile {
  id: string
  filename: string
  size: number
  format: LogFormat
  upload_time: string
  status: string
  analysis?: LogAnalysis
  entry_count?: number
}

export enum LogFormat {
  JSON = 'json',
  CSV = 'csv',
  SYSLOG = 'syslog',
  PLAIN_TEXT = 'plain_text',
  CUSTOM = 'custom'
}

export enum LogLevel {
  ERROR = 'ERROR',
  WARN = 'WARN',
  WARNING = 'WARNING',
  INFO = 'INFO',
  DEBUG = 'DEBUG',
  TRACE = 'TRACE',
  FATAL = 'FATAL',
  CRITICAL = 'CRITICAL'
}

export interface LogEntry {
  timestamp?: string
  level?: LogLevel
  service?: string
  message: string
  raw_line: string
  line_number: number
  metadata?: Record<string, any>
}

export interface LogAnalysis {
  total_entries: number
  date_range: {
    start?: string
    end?: string
  }
  level_distribution: Record<LogLevel, number>
  service_distribution: Record<string, number>
  error_patterns: PatternMatch[]
  anomalies: Anomaly[]
  time_series: TimeSeriesData[]
}

export interface PatternMatch {
  pattern: string
  count: number
  examples: string[]
  severity: string
  category: string
  first_occurrence?: string
  last_occurrence?: string
}

export interface Anomaly {
  type: string
  description: string
  timestamp: string
  severity: 'low' | 'medium' | 'high'
  affected_entries: number
}

export interface TimeSeriesData {
  timestamp: string
  error_count: number
  warn_count: number
  info_count: number
  total_count: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ChatRequest {
  message: string
  file_id?: string
  context?: ChatMessage[]
}

export interface ChatResponse {
  response: string
  context: ChatMessage[]
  suggested_questions?: string[]
}

export interface FileUploadResponse {
  id: string
  filename: string
  size: number
  format: LogFormat
  upload_time: string
  status: string
}

export interface ApiError {
  detail: string
  error_type: string
  timestamp: string
}