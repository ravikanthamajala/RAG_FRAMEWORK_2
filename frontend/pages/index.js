/*
 * Home page component for the Agentic RAG Document Assistant.
 * Displays file upload, query forms, and ML forecasting features.
 */

import { useState } from 'react'
import FileUpload from '../components/FileUpload'
import QueryForm from '../components/QueryForm'
import SmartUploadForecast from '../components/SmartUploadForecast'

export default function Home() {
  const [activeTab, setActiveTab] = useState('query') // 'query' or 'forecast'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-4xl font-bold mb-2">🚀 Agentic RAG Document Assistant</h1>
          <p className="text-blue-100">AI-powered document analysis with machine learning forecasting</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('query')}
              className={`py-4 font-semibold border-b-2 transition ${
                activeTab === 'query'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              📄 Document Query
            </button>
            <button
              onClick={() => setActiveTab('forecast')}
              className={`py-4 font-semibold border-b-2 transition ${
                activeTab === 'forecast'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              📊 ML Forecasting
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        {activeTab === 'query' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div>
              <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
              <FileUpload />
            </div>
            
            <div className="lg:col-span-2">
              <h2 className="text-xl font-semibold mb-4">Query Documents</h2>
              <QueryForm />
            </div>
          </div>
        ) : (
          <SmartUploadForecast />
        )}
      </div>
    </div>
  )
}