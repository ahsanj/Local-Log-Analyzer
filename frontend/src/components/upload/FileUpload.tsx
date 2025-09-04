import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFileStore } from '../../hooks/useFileStore'
import { LogFormat } from '../../types'
import FileUploadZone from './FileUploadZone'
import PasteTextArea from './PasteTextArea'
import { FileInfo } from '../../utils/fileUtils'
import clsx from 'clsx'

export default function FileUpload() {
  const navigate = useNavigate()
  const { uploadFile, pasteContent, isLoading } = useFileStore()
  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload')

  const handleFileSelect = async (file: File, _fileInfo: FileInfo) => {
    const response = await uploadFile(file)
    if (response) {
      navigate(`/dashboard/${response.id}`)
    }
  }

  const handleContentSubmit = async (content: string, _format: LogFormat) => {
    const response = await pasteContent(content)
    if (response) {
      navigate(`/dashboard/${response.id}`)
    }
  }

  return (
    <div className="flex-1 overflow-hidden">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 text-center py-8 px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Upload Your Log Files
          </h1>
          <p className="text-lg text-gray-600">
            Analyze logs privately with local AI processing
          </p>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden px-8 pb-8">
          <div className="max-w-4xl mx-auto h-full">
            <div className="card h-full flex flex-col">
              {/* Tabs */}
              <div className="flex-shrink-0 flex border-b border-gray-200">
                <button
                  onClick={() => setActiveTab('upload')}
                  className={clsx(
                    'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                    activeTab === 'upload'
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  )}
                >
                  📁 Upload File
                </button>
                <button
                  onClick={() => setActiveTab('paste')}
                  className={clsx(
                    'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                    activeTab === 'paste'
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  )}
                >
                  📋 Paste Content
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden">
                {activeTab === 'upload' && (
                  <div className="p-8 h-full overflow-y-auto">
                    <FileUploadZone 
                      onFileSelect={handleFileSelect}
                      isUploading={isLoading}
                    />
                    
                    {/* Security Features */}
                    <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                        <span>Secure local processing</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full" />
                        <span>No data transmitted externally</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full" />
                        <span>AI-powered analysis</span>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'paste' && (
                  <div className="p-8 h-full overflow-y-auto">
                    <PasteTextArea 
                      onContentSubmit={handleContentSubmit}
                      isUploading={isLoading}
                    />
                  </div>
                )}
              </div>

              {/* Loading Indicator */}
              {isLoading && (
                <div className="flex-shrink-0 border-t border-gray-200 p-4">
                  <div className="flex items-center justify-center space-x-2 text-primary-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
                    <span className="text-sm font-medium">Processing and analyzing your data...</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}