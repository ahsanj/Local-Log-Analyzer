import { create } from 'zustand'
import { LogFile, FileUploadResponse } from '../types'
import { fileApi } from '../services/api'
import toast from 'react-hot-toast'

interface FileStore {
  files: LogFile[]
  selectedFile: LogFile | null
  isLoading: boolean
  error: string | null
  
  // Actions
  loadFiles: () => Promise<void>
  uploadFile: (file: File) => Promise<FileUploadResponse | null>
  pasteContent: (content: string) => Promise<FileUploadResponse | null>
  selectFile: (fileId: string) => Promise<void>
  deleteFile: (fileId: string) => Promise<void>
  clearError: () => void
}

export const useFileStore = create<FileStore>((set, get) => ({
  files: [],
  selectedFile: null,
  isLoading: false,
  error: null,

  loadFiles: async () => {
    set({ isLoading: true, error: null })
    try {
      const files = await fileApi.getFiles()
      set({ files, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load files'
      set({ error: errorMessage, isLoading: false })
      toast.error(errorMessage)
    }
  },

  uploadFile: async (file: File) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fileApi.uploadFile(file)
      
      // Reload files to get updated list
      await get().loadFiles()
      
      toast.success(`File "${file.name}" uploaded successfully`)
      set({ isLoading: false })
      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload file'
      set({ error: errorMessage, isLoading: false })
      toast.error(errorMessage)
      return null
    }
  },

  pasteContent: async (content: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fileApi.pasteContent(content)
      
      // Reload files to get updated list
      await get().loadFiles()
      
      toast.success('Content pasted successfully')
      set({ isLoading: false })
      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to paste content'
      set({ error: errorMessage, isLoading: false })
      toast.error(errorMessage)
      return null
    }
  },

  selectFile: async (fileId: string) => {
    set({ isLoading: true, error: null })
    try {
      const file = await fileApi.getFile(fileId)
      set({ selectedFile: file, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load file details'
      set({ error: errorMessage, isLoading: false })
      toast.error(errorMessage)
    }
  },

  deleteFile: async (fileId: string) => {
    set({ isLoading: true, error: null })
    try {
      await fileApi.deleteFile(fileId)
      
      // Remove from local state
      const { files, selectedFile } = get()
      const updatedFiles = files.filter(f => f.id !== fileId)
      const newSelectedFile = selectedFile?.id === fileId ? null : selectedFile
      
      set({ 
        files: updatedFiles, 
        selectedFile: newSelectedFile,
        isLoading: false 
      })
      
      toast.success('File deleted successfully')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete file'
      set({ error: errorMessage, isLoading: false })
      toast.error(errorMessage)
    }
  },

  clearError: () => set({ error: null }),
}))