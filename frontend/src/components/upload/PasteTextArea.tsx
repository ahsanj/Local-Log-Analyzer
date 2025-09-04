import { useState, useRef, useCallback } from 'react'
import { 
  ClipboardDocumentIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
  EyeIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline'
import { 
  validatePasteContent, 
  detectLogFormat, 
  formatFileSize, 
  getFormatDescription,
  getFormatIcon,
  generatePreviewLines,
  FileValidationResult
} from '../../utils/fileUtils'
import { LogFormat } from '../../types'
import clsx from 'clsx'

interface PasteTextAreaProps {
  onContentSubmit: (content: string, format: LogFormat) => void
  isUploading: boolean
  className?: string
}

export default function PasteTextArea({ onContentSubmit, isUploading, className }: PasteTextAreaProps) {
  const [content, setContent] = useState('')
  const [validation, setValidation] = useState<FileValidationResult | null>(null)
  const [detectedFormat, setDetectedFormat] = useState<LogFormat | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const validateContent = useCallback((text: string) => {
    if (text.length === 0) {
      setValidation(null)
      setDetectedFormat(null)
      return
    }

    const validationResult = validatePasteContent(text)
    const format = detectLogFormat('pasted_content.log', text)
    
    setValidation(validationResult)
    setDetectedFormat(format)
  }, [])

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value
    setContent(newContent)
    
    // Debounce validation for performance
    const timeoutId = setTimeout(() => {
      validateContent(newContent)
    }, 500)

    return () => clearTimeout(timeoutId)
  }

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Allow default paste behavior, then validate
    setTimeout(() => {
      validateContent(e.currentTarget.value)
    }, 0)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validation?.isValid && detectedFormat) {
      onContentSubmit(content, detectedFormat)
      handleClear()
    }
  }

  const handleClear = () => {
    setContent('')
    setValidation(null)
    setDetectedFormat(null)
    setShowPreview(false)
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }

  const handleLoadSample = () => {
    const sampleContent = `2024-08-24 10:30:15 [INFO] Application started successfully
2024-08-24 10:30:16 [INFO] Database connection established
2024-08-24 10:30:17 [WARN] High memory usage detected: 85%
2024-08-24 10:31:20 [ERROR] Failed to process user request: timeout
2024-08-24 10:31:21 [INFO] Retrying request with exponential backoff
2024-08-24 10:31:25 [INFO] Request processed successfully
2024-08-24 10:32:10 [ERROR] Database connection lost
2024-08-24 10:32:11 [INFO] Attempting database reconnection
2024-08-24 10:32:15 [INFO] Database reconnected successfully`
    
    setContent(sampleContent)
    validateContent(sampleContent)
  }

  const contentSize = new Blob([content]).size
  const lineCount = content.split('\n').length
  const previewLines = generatePreviewLines(content, 5)

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ClipboardDocumentIcon className="h-5 w-5 text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900">Paste Log Content</h3>
        </div>
        
        {content.length === 0 && (
          <button
            onClick={handleLoadSample}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Load Sample Data
          </button>
        )}
      </div>

      {/* Main Text Area */}
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleContentChange}
            onPaste={handlePaste}
            placeholder={`Paste your log entries here...

Examples:
• 2024-01-01 12:00:00 [ERROR] Connection failed
• {"timestamp":"2024-01-01T12:00:00Z","level":"INFO","message":"Started"}
• timestamp,level,service,message`}
            disabled={isUploading}
            className={clsx(
              'w-full px-4 py-3 border rounded-lg font-mono text-sm resize-none transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              {
                'h-32': !isExpanded && content.length === 0,
                'h-48': !isExpanded && content.length > 0,
                'h-80': isExpanded,
                'bg-gray-50 cursor-not-allowed': isUploading,
                'border-gray-300': !validation,
                'border-success-300': validation?.isValid,
                'border-error-300': validation && !validation.isValid,
              }
            )}
          />
          
          {/* Expand/Collapse Button */}
          {content.length > 0 && (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              <ArrowDownTrayIcon className={clsx('h-4 w-4 transition-transform', {
                'rotate-180': isExpanded
              })} />
            </button>
          )}
        </div>

        {/* Content Stats */}
        {content.length > 0 && (
          <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span>{formatFileSize(contentSize)}</span>
              <span>•</span>
              <span>{lineCount.toLocaleString()} lines</span>
              {detectedFormat && (
                <>
                  <span>•</span>
                  <span className="flex items-center space-x-1">
                    <span>{getFormatIcon(detectedFormat)}</span>
                    <span className="capitalize">{detectedFormat.replace('_', ' ')}</span>
                  </span>
                </>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {content.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowPreview(!showPreview)}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Toggle preview"
                >
                  <EyeIcon className="h-4 w-4" />
                </button>
              )}
              
              <button
                type="button"
                onClick={handleClear}
                className="p-1 text-gray-400 hover:text-error-600 transition-colors"
                title="Clear content"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Format Description */}
        {detectedFormat && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-start space-x-2">
              <InformationCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h5 className="text-sm font-medium text-blue-800">
                  Detected Format: {detectedFormat.replace('_', ' ').toUpperCase()}
                </h5>
                <p className="mt-1 text-sm text-blue-700">
                  {getFormatDescription(detectedFormat)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Validation Messages */}
        {validation?.errors && validation.errors.length > 0 && (
          <div className="mt-3 p-3 bg-error-100 rounded-lg">
            <div className="flex items-start space-x-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-error-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h5 className="text-sm font-medium text-error-800">Validation Errors</h5>
                <ul className="mt-1 text-sm text-error-700 space-y-1">
                  {validation.errors.map((error, index) => (
                    <li key={index} className="flex items-start space-x-1">
                      <span>•</span>
                      <span>{error}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Validation Warnings */}
        {validation?.warnings && validation.warnings.length > 0 && (
          <div className="mt-3 p-3 bg-warning-100 rounded-lg">
            <div className="flex items-start space-x-2">
              <InformationCircleIcon className="h-5 w-5 text-warning-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h5 className="text-sm font-medium text-warning-800">Warnings</h5>
                <ul className="mt-1 text-sm text-warning-700 space-y-1">
                  {validation.warnings.map((warning, index) => (
                    <li key={index} className="flex items-start space-x-1">
                      <span>•</span>
                      <span>{warning}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Preview */}
        {showPreview && content.length > 0 && (
          <div className="mt-3 p-3 bg-gray-100 rounded-lg">
            <h5 className="text-sm font-medium text-gray-800 mb-2">Content Preview (first 5 lines)</h5>
            <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap">
              {previewLines.join('\n')}
              {lineCount > 5 && '\n... and ' + (lineCount - 5) + ' more lines'}
            </pre>
          </div>
        )}

        {/* Submit Button */}
        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            disabled={!validation?.isValid || isUploading}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <ClipboardDocumentIcon className="h-4 w-4" />
            <span>{isUploading ? 'Processing...' : 'Analyze Content'}</span>
          </button>
        </div>
      </form>

      {/* Tips */}
      {content.length === 0 && (
        <div className="text-sm text-gray-500 space-y-2">
          <p className="font-medium">💡 Tips for better analysis:</p>
          <ul className="space-y-1 ml-4">
            <li>• Include timestamps for timeline analysis</li>
            <li>• Paste complete log entries (avoid truncated lines)</li>
            <li>• Include log levels (ERROR, WARN, INFO) for categorization</li>
            <li>• Multiple formats are supported: plain text, JSON, CSV, syslog</li>
          </ul>
        </div>
      )}
    </div>
  )
}