import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { 
  DocumentArrowUpIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import { 
  validateFile, 
  getFileInfo, 
  formatFileSize, 
  getFormatDescription,
  getFormatIcon,
  isTextFile,
  FileValidationResult,
  FileInfo
} from '../../utils/fileUtils'
import clsx from 'clsx'

interface FileUploadZoneProps {
  onFileSelect: (file: File, fileInfo: FileInfo) => void
  isUploading: boolean
  className?: string
}

interface FileWithValidation {
  file: File
  validation: FileValidationResult
  info?: FileInfo
}

export default function FileUploadZone({ onFileSelect, isUploading, className }: FileUploadZoneProps) {
  const [selectedFiles, setSelectedFiles] = useState<FileWithValidation[]>([])
  const [showPreview, setShowPreview] = useState<string | null>(null)

  const processFiles = useCallback(async (files: File[]) => {
    const processedFiles: FileWithValidation[] = []
    
    for (const file of files) {
      const validation = validateFile(file)
      let info: FileInfo | undefined

      if (validation.isValid && isTextFile(file)) {
        try {
          info = await getFileInfo(file)
        } catch (error) {
          console.warn('Failed to get file info:', error)
        }
      }

      processedFiles.push({ file, validation, info })
    }

    setSelectedFiles(processedFiles)
  }, [])

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle accepted files
    if (acceptedFiles.length > 0) {
      processFiles(acceptedFiles)
    }

    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const rejectedProcessed = rejectedFiles.map(({ file, errors }) => ({
        file,
        validation: {
          isValid: false,
          errors: errors.map((e: any) => e.message),
          warnings: []
        }
      }))
      setSelectedFiles(prev => [...prev, ...rejectedProcessed])
    }
  }, [processFiles])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    multiple: false, // Only allow one file at a time
    disabled: isUploading,
    accept: {
      'text/plain': ['.log', '.txt'],
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'application/csv': ['.csv'],
      'text/x-log': ['.syslog']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const handleUpload = (fileWithValidation: FileWithValidation) => {
    if (fileWithValidation.validation.isValid && fileWithValidation.info) {
      onFileSelect(fileWithValidation.file, fileWithValidation.info)
      setSelectedFiles([]) // Clear selection after upload
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const togglePreview = (fileName: string) => {
    setShowPreview(showPreview === fileName ? null : fileName)
  }

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Drag & Drop Zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer',
          {
            'border-primary-400 bg-primary-50': isDragActive && !isDragReject,
            'border-error-400 bg-error-50': isDragReject,
            'border-gray-300 hover:border-gray-400 bg-gray-50': !isDragActive && !isUploading,
            'border-gray-200 bg-gray-100 cursor-not-allowed': isUploading,
          }
        )}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 flex items-center justify-center">
            {isUploading ? (
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            ) : (
              <DocumentArrowUpIcon 
                className={clsx('h-12 w-12', {
                  'text-primary-500': isDragActive && !isDragReject,
                  'text-error-500': isDragReject,
                  'text-gray-400': !isDragActive,
                })} 
              />
            )}
          </div>

          <div>
            {isUploading ? (
              <p className="text-lg text-gray-600 font-medium">Processing file...</p>
            ) : isDragActive ? (
              isDragReject ? (
                <p className="text-lg text-error-600 font-medium">
                  File type not supported
                </p>
              ) : (
                <p className="text-lg text-primary-600 font-medium">
                  Drop the file here...
                </p>
              )
            ) : (
              <div>
                <p className="text-lg text-gray-600 mb-2">
                  Drag & drop a log file here, or <span className="text-primary-600 font-medium">click to browse</span>
                </p>
                <p className="text-sm text-gray-500">
                  Supports .log, .txt, .csv, .json, .syslog files up to 50MB
                </p>
              </div>
            )}
          </div>

          {/* File type indicators */}
          <div className="flex justify-center space-x-4 text-sm text-gray-500">
            <span className="flex items-center space-x-1">
              <span>📄</span>
              <span>.log .txt</span>
            </span>
            <span className="flex items-center space-x-1">
              <span>{ }</span>
              <span>.json</span>
            </span>
            <span className="flex items-center space-x-1">
              <span>📊</span>
              <span>.csv</span>
            </span>
            <span className="flex items-center space-x-1">
              <span>🖥️</span>
              <span>.syslog</span>
            </span>
          </div>
        </div>
      </div>

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-gray-900">Selected Files</h3>
          {selectedFiles.map((fileWithValidation, index) => (
            <FilePreviewCard
              key={`${fileWithValidation.file.name}-${index}`}
              fileWithValidation={fileWithValidation}
              onUpload={() => handleUpload(fileWithValidation)}
              onRemove={() => removeFile(index)}
              onTogglePreview={() => togglePreview(fileWithValidation.file.name)}
              showPreview={showPreview === fileWithValidation.file.name}
              isUploading={isUploading}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface FilePreviewCardProps {
  fileWithValidation: FileWithValidation
  onUpload: () => void
  onRemove: () => void
  onTogglePreview: () => void
  showPreview: boolean
  isUploading: boolean
}

function FilePreviewCard({ 
  fileWithValidation, 
  onUpload, 
  onRemove, 
  onTogglePreview, 
  showPreview,
  isUploading 
}: FilePreviewCardProps) {
  const { file, validation, info } = fileWithValidation

  return (
    <div className={clsx(
      'border rounded-lg p-4 transition-all duration-200',
      validation.isValid 
        ? 'border-success-200 bg-success-50' 
        : 'border-error-200 bg-error-50'
    )}>
      {/* File Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1 min-w-0">
          {/* File Icon */}
          <div className="flex-shrink-0">
            {info && (
              <span className="text-2xl" title={getFormatDescription(info.format)}>
                {getFormatIcon(info.format)}
              </span>
            )}
          </div>

          {/* File Info */}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-gray-900 truncate">
              {file.name}
            </h4>
            <div className="flex items-center space-x-4 mt-1 text-xs text-gray-600">
              <span>{formatFileSize(file.size)}</span>
              {info && (
                <>
                  <span>•</span>
                  <span className="capitalize">{info.format.replace('_', ' ')}</span>
                </>
              )}
              <span>•</span>
              <span>{new Date(file.lastModified).toLocaleDateString()}</span>
            </div>
            {info && (
              <p className="text-xs text-gray-500 mt-1">
                {getFormatDescription(info.format)}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          {validation.isValid && info?.preview && (
            <button
              onClick={onTogglePreview}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Toggle preview"
            >
              <EyeIcon className="h-4 w-4" />
            </button>
          )}
          
          <button
            onClick={onRemove}
            className="p-2 text-gray-400 hover:text-error-600 transition-colors"
            title="Remove file"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Validation Messages */}
      {validation.errors.length > 0 && (
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
      {validation.warnings.length > 0 && (
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

      {/* File Preview */}
      {showPreview && info?.preview && (
        <div className="mt-3 p-3 bg-gray-100 rounded-lg">
          <h5 className="text-sm font-medium text-gray-800 mb-2">Preview (first 500 characters)</h5>
          <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap overflow-x-auto max-h-40 overflow-y-auto">
            {info.preview}
          </pre>
        </div>
      )}

      {/* Upload Button */}
      {validation.isValid && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={onUpload}
            disabled={isUploading}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? 'Uploading...' : 'Analyze File'}
          </button>
        </div>
      )}
    </div>
  )
}