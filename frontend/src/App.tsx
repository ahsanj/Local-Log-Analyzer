import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './components/dashboard/Dashboard'
import FileUpload from './components/upload/FileUpload'
import { useFileStore } from './hooks/useFileStore'
import { useEffect } from 'react'

function App() {
  const { loadFiles } = useFileStore()

  useEffect(() => {
    // Load existing files on app start
    loadFiles()
  }, [loadFiles])

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<FileUpload />} />
          <Route path="dashboard/:fileId" element={<Dashboard />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App