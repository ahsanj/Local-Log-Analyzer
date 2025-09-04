import axios from 'axios'
import { 
  LogFile, 
  FileUploadResponse, 
  LogAnalysis, 
  PatternMatch,
  ChatRequest,
  ChatResponse,
  LogEntry
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 120000, // 2 minutes for large file processing
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    }
    throw error
  }
)

export const fileApi = {
  uploadFile: async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  pasteContent: async (content: string): Promise<FileUploadResponse> => {
    const response = await api.post('/files/paste', { content })
    return response.data
  },

  getFiles: async (): Promise<LogFile[]> => {
    const response = await api.get('/files/')
    return response.data
  },

  getFile: async (fileId: string): Promise<LogFile> => {
    const response = await api.get(`/files/${fileId}`)
    return response.data
  },

  deleteFile: async (fileId: string): Promise<void> => {
    await api.delete(`/files/${fileId}`)
  },
}

export const analysisApi = {
  analyzeFile: async (fileId: string): Promise<LogAnalysis> => {
    const response = await api.post(`/analysis/${fileId}`)
    return response.data
  },

  getPatterns: async (fileId: string): Promise<PatternMatch[]> => {
    const response = await api.get(`/analysis/${fileId}/patterns`)
    return response.data
  },

  getStats: async (fileId: string): Promise<any> => {
    const response = await api.get(`/analysis/${fileId}/stats`)
    return response.data
  },

  getEntries: async (
    fileId: string, 
    options: {
      offset?: number
      limit?: number
      level?: string
      service?: string
      search?: string
    } = {}
  ): Promise<{ entries: LogEntry[], total: number }> => {
    const params = new URLSearchParams()
    if (options.offset !== undefined) params.append('offset', options.offset.toString())
    if (options.limit !== undefined) params.append('limit', options.limit.toString())
    if (options.level) params.append('level', options.level)
    if (options.service) params.append('service', options.service)
    if (options.search) params.append('search', options.search)

    const response = await api.get(`/analysis/${fileId}/entries?${params}`)
    return response.data
  },

  getTimeline: async (fileId: string, interval: string = '1h'): Promise<any> => {
    const response = await api.get(`/analysis/${fileId}/timeline?interval=${interval}`)
    return response.data
  },
}

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat/', request)
    return response.data
  },

  getHistory: async (sessionId: string): Promise<any> => {
    const response = await api.get(`/chat/history/${sessionId}`)
    return response.data
  },

  getSession: async (fileId: string): Promise<{
    file_id: string
    session_id: string
    chat_history: any[]
    has_context: boolean
    total_entries: number
  }> => {
    const response = await api.get(`/chat/session/${fileId}`)
    return response.data
  },

  clearHistory: async (sessionId: string): Promise<void> => {
    await api.delete(`/chat/history/${sessionId}`)
  },

  getSuggestions: async (fileId: string): Promise<{ suggestions: string[] }> => {
    const response = await api.get(`/chat/suggestions/${fileId}`)
    return response.data
  },
}

export const healthApi = {
  checkHealth: async (): Promise<{ status: string, version: string }> => {
    const response = await api.get('/health')
    return response.data
  },
}

export default api