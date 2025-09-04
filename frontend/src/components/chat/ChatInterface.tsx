import { useState, useEffect, useRef } from 'react'
import { chatApi } from '../../services/api'
import { ChatMessage } from '../../types'
import { PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface ChatInterfaceProps {
  fileId: string
}

export default function ChatInterface({ fileId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadChatSession()
    loadSuggestions()
  }, [fileId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadChatSession = async () => {
    try {
      console.log('🔄 Loading chat session for fileId:', fileId)
      const sessionData = await chatApi.getSession(fileId)
      
      if (sessionData.chat_history && sessionData.chat_history.length > 0) {
        console.log('✅ Loaded chat history:', sessionData.chat_history.length, 'messages')
        setMessages(sessionData.chat_history)
      } else {
        console.log('ℹ️ No existing chat history found')
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to load chat session:', error)
      // If session loading fails, start with empty messages (new session)
      setMessages([])
    }
  }

  const loadSuggestions = async () => {
    try {
      const response = await chatApi.getSuggestions(fileId)
      setSuggestions(response.suggestions)
    } catch (error) {
      console.error('Failed to load suggestions:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return

    const newMessage = message.trim()
    setInputMessage('')
    setIsLoading(true)

    // Add user message immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: newMessage,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const response = await chatApi.sendMessage({
        message: newMessage,
        file_id: fileId,
        context: messages
      })

      // Use the complete context from server response if available
      if (response.context && response.context.length > 0) {
        console.log('✅ Updated chat context from server:', response.context.length, 'messages')
        setMessages(response.context)
      } else {
        // Fallback: Add AI response manually
        const aiMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, aiMessage])
      }

      // Update suggestions if provided
      if (response.suggested_questions) {
        setSuggestions(response.suggested_questions)
      }
    } catch (error) {
      console.error('Chat failed:', error)
      
      // Add error message
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error while analyzing your request. Please make sure Ollama is running with the CodeLlama 13B model.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(inputMessage)
  }

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <SparklesIcon className="h-12 w-12 text-primary-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              AI Log Analysis
            </h3>
            <p className="text-gray-600 mb-6 max-w-md">
              Ask questions about your log data. I can help you find patterns, analyze errors, 
              and understand what's happening in your system.
            </p>
            
            {suggestions.length > 0 && (
              <div className="w-full max-w-2xl">
                <p className="text-sm text-gray-500 mb-3">Try asking:</p>
                <div className="grid gap-2">
                  {suggestions.slice(0, 4).map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="p-3 text-left text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={clsx(
                  'flex',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={clsx(
                    'max-w-3xl px-4 py-3 rounded-lg',
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  <div className="whitespace-pre-wrap text-sm">
                    {message.content}
                  </div>
                  <div
                    className={clsx(
                      'text-xs mt-2',
                      message.role === 'user' ? 'text-primary-200' : 'text-gray-500'
                    )}
                  >
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-3xl px-4 py-3 bg-gray-100 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                    <span className="text-sm text-gray-600">Analyzing...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Suggestions (shown when there are messages) */}
      {messages.length > 0 && suggestions.length > 0 && !isLoading && (
        <div className="border-t border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-2">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 3).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask me about your logs..."
            disabled={isLoading}
            className="flex-1 input-field disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <PaperAirplaneIcon className="h-4 w-4" />
            <span>Send</span>
          </button>
        </form>
        
        <p className="text-xs text-gray-500 mt-2">
          💡 Powered by CodeLlama 13B running locally via Ollama
        </p>
      </div>
    </div>
  )
}