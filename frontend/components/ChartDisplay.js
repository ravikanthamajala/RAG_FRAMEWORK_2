/*
 * ChartDisplay component for rendering visualizations
 * Displays bar charts, line charts, and pie charts from the RAG agent
 * Features: fullscreen modal, download PNG, grid/stack layout toggle, hover tooltips
 */

import { useState } from 'react'

function ChartCard({ chart, onFullscreen, onDownload }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className="bg-white border border-gray-200 rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Card header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-4">
        <div className="flex justify-between items-start gap-3">
          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-lg leading-tight">{chart.title}</h4>
            {chart.description && (
              <p className="text-blue-100 text-sm mt-1 leading-snug">{chart.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onDownload}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-2 transition-all"
              title="Download chart as PNG"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              onClick={onFullscreen}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-2 transition-all"
              title="View fullscreen"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Chart image area */}
      <div className="relative p-5 bg-gray-50 flex-1">
        <img
          src={chart.image}
          alt={chart.title}
          className="w-full h-auto rounded-lg cursor-zoom-in"
          style={{ minHeight: '320px', maxHeight: '480px', objectFit: 'contain' }}
          onClick={onFullscreen}
        />
        {hovered && (
          <div className="absolute bottom-7 right-7 pointer-events-none">
            <span className="bg-black bg-opacity-55 text-white text-xs px-2.5 py-1 rounded-md">
              Click to expand
            </span>
          </div>
        )}
      </div>

      {/* Card footer */}
      <div className="px-5 py-3 bg-white border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="capitalize font-medium">{chart.type} chart</span>
        </div>
        <button
          onClick={onFullscreen}
          className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 transition"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
          Fullscreen
        </button>
      </div>
    </div>
  )
}

export default function ChartDisplay({ charts }) {
  const [fullscreenIndex, setFullscreenIndex] = useState(null)
  const [layout, setLayout] = useState('grid') // 'grid' | 'stack'

  if (!charts || charts.length === 0) return null

  const downloadChart = (chart, index) => {
    const link = document.createElement('a')
    link.href = chart.image
    link.download = `chart-${index + 1}-${(chart.title || 'chart').replace(/\s+/g, '-').toLowerCase()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const fullscreenChart = fullscreenIndex !== null ? charts[fullscreenIndex] : null

  return (
    <div className="mt-8">
      <div className="border-t pt-6">

        {/* Section header */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <h3 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <svg className="w-7 h-7 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Visual Analysis
            <span className="bg-blue-100 text-blue-700 text-sm font-semibold px-3 py-0.5 rounded-full">
              {charts.length} chart{charts.length !== 1 ? 's' : ''}
            </span>
          </h3>

          {/* Layout toggle */}
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1 text-sm">
            <button
              onClick={() => setLayout('stack')}
              className={`px-3 py-1.5 rounded font-medium transition-all ${layout === 'stack' ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-800'}`}
              title="Full-width stacked layout"
            >
              ☰ Stack
            </button>
            <button
              onClick={() => setLayout('grid')}
              className={`px-3 py-1.5 rounded font-medium transition-all ${layout === 'grid' ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-800'}`}
              title="2-column grid layout"
            >
              ⊞ Grid
            </button>
          </div>
        </div>

        {/* Charts container — responsive: mobile=1col, tablet=1col, desktop=2col (grid) */}
        <div className={
          layout === 'grid'
            ? 'grid grid-cols-1 xl:grid-cols-2 gap-6'
            : 'flex flex-col gap-6'
        }>
          {charts.map((chart, index) => (
            <ChartCard
              key={index}
              chart={chart}
              onFullscreen={() => setFullscreenIndex(index)}
              onDownload={() => downloadChart(chart, index)}
            />
          ))}
        </div>
      </div>

      {/* Fullscreen Modal */}
      {fullscreenChart && (
        <div
          className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setFullscreenIndex(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[95vh] overflow-auto flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-5 rounded-t-2xl flex justify-between items-start gap-3 shrink-0">
              <div>
                <h4 className="font-bold text-xl">{fullscreenChart.title}</h4>
                {fullscreenChart.description && (
                  <p className="text-blue-100 text-sm mt-1">{fullscreenChart.description}</p>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => downloadChart(fullscreenChart, fullscreenIndex)}
                  className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg px-3 py-2 text-sm font-semibold flex items-center gap-1.5 transition"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </button>
                <button
                  onClick={() => setFullscreenIndex(null)}
                  className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full w-9 h-9 flex items-center justify-center text-xl leading-none font-bold transition"
                  title="Close"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Modal body */}
            <div className="p-8 bg-gray-50 rounded-b-2xl">
              <img
                src={fullscreenChart.image}
                alt={fullscreenChart.title}
                className="w-full h-auto rounded-xl shadow-md"
              />
              <p className="text-center text-sm text-gray-400 mt-4 capitalize">
                {fullscreenChart.type} chart · Click outside or press × to close
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
