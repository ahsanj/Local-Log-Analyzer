import { useEffect, useState } from 'react'
import { ChartBarIcon, Cog6ToothIcon } from '@heroicons/react/24/outline'
import { healthApi } from '../../services/api'

export default function Header() {
  const [isOnline, setIsOnline] = useState(false)
  const [version, setVersion] = useState('')

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await healthApi.checkHealth()
        setIsOnline(health.status === 'healthy')
        setVersion(health.version)
      } catch (error) {
        setIsOnline(false)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-8 w-8 text-primary-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Local Log Analyzer</h1>
            <p className="text-sm text-gray-500">Privacy-first log analysis</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-success-500' : 'bg-error-500'}`} />
            <span className="text-sm text-gray-600">
              {isOnline ? 'Connected' : 'Offline'}
            </span>
            {version && (
              <span className="text-xs text-gray-400">v{version}</span>
            )}
          </div>
          
          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <Cog6ToothIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  )
}