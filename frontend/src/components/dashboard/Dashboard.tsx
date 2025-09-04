import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useFileStore } from '../../hooks/useFileStore'
import { analysisApi } from '../../services/api'
import { LogAnalysis } from '../../types'
import OverviewCards from './OverviewCards'
import TimelineChart from './TimelineChart'
import PatternsList from './PatternsList'
import ChatInterface from '../chat/ChatInterface'
import LogEntries from './LogEntries'

export default function Dashboard() {
  const { fileId } = useParams<{ fileId: string }>()
  const { selectedFile, selectFile } = useFileStore()
  const [analysis, setAnalysis] = useState<LogAnalysis | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'entries' | 'chat'>('overview')

  useEffect(() => {
    if (fileId) {
      loadFileAndAnalysis(fileId)
    }
  }, [fileId])

  const loadFileAndAnalysis = async (id: string) => {
    await selectFile(id)
    
    setIsAnalyzing(true)
    try {
      const analysisResult = await analysisApi.analyzeFile(id)
      setAnalysis(analysisResult)
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  if (!selectedFile) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <p>Loading file...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 truncate">
              {selectedFile.filename}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {selectedFile.format.toUpperCase()} • {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
              {analysis && ` • ${analysis.total_entries.toLocaleString()} entries`}
            </p>
          </div>
          
          {isAnalyzing && (
            <div className="flex items-center space-x-2 text-primary-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
              <span className="text-sm">Analyzing...</span>
            </div>
          )}
        </div>
        
        {/* Tabs */}
        <div className="mt-4 flex space-x-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'overview'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('entries')}
            className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'entries'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Log Entries
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'chat'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            AI Analysis
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'overview' && (
          <div className="h-full overflow-y-auto p-6">
            {analysis ? (
              <div className="space-y-6">
                <OverviewCards analysis={analysis} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <TimelineChart data={analysis.time_series} />
                  <PatternsList patterns={analysis.error_patterns} />
                </div>
              </div>
            ) : isAnalyzing ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4" />
                  <p className="text-gray-600">Analyzing log file...</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64">
                <div className="text-center text-gray-500">
                  <p>No analysis data available</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'entries' && (
          <LogEntries fileId={fileId!} />
        )}

        {activeTab === 'chat' && (
          <ChatInterface fileId={fileId!} />
        )}
      </div>
    </div>
  )
}