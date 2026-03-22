/*
 * QueryForm component for submitting queries to the RAG agent.
 * Displays a form to input queries and shows structured, intent-aware responses
 * with optional chart visualizations.
 */

import { useState } from 'react'
import axios from 'axios'
import ChartDisplay from './ChartDisplay'

const PRIMARY_API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:4000'
const FALLBACK_API_BASE = PRIMARY_API_BASE.includes('localhost')
  ? PRIMARY_API_BASE.replace('localhost', '127.0.0.1')
  : PRIMARY_API_BASE.includes('127.0.0.1')
    ? PRIMARY_API_BASE.replace('127.0.0.1', 'localhost')
    : 'http://127.0.0.1:4000'

// â”€â”€â”€ Lightweight structured-response renderer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const INTENT_META = {
  COMPARISON:   { label: 'Comparison',   color: 'bg-purple-100 text-purple-800' },
  FORECAST:     { label: 'Forecast',     color: 'bg-blue-100 text-blue-800'   },
  TREND:        { label: 'Trend',        color: 'bg-teal-100 text-teal-800'   },
  NUMBERS:      { label: 'Quantitative', color: 'bg-orange-100 text-orange-800' },
  DISTRIBUTION: { label: 'Distribution', color: 'bg-pink-100 text-pink-800'  },
  GENERAL:      { label: 'General',      color: 'bg-gray-100 text-gray-700'   },
}

/** Render one table row/header line from a pipe-delimited markdown string. */
function MarkdownTableRow({ line, isHeader }) {
  const cells = line.split('|').filter((_, i, a) => i > 0 && i < a.length - 1)
  const Tag = isHeader ? 'th' : 'td'
  return (
    <tr className={isHeader ? 'bg-gray-100' : 'even:bg-gray-50'}>
      {cells.map((cell, i) => (
        <Tag
          key={i}
          className={`px-4 py-2 text-sm border border-gray-200 ${
            isHeader ? 'font-bold text-gray-700' : 'text-gray-800'
          } ${i > 0 ? 'text-right' : 'text-left'}`}
        >
          {cell.trim()}
        </Tag>
      ))}
    </tr>
  )
}

/** Parse raw markdown text into renderable React blocks. */
function StructuredResponse({ text }) {
  if (!text) return null

  const lines = text.split('\n')
  const blocks = []
  let tableLines = []
  let inTable = false

  const flushTable = () => {
    if (!tableLines.length) return
    const [headerLine, _sep, ...bodyLines] = tableLines
    blocks.push(
      <div key={`tbl-${blocks.length}`} className="overflow-x-auto my-3">
        <table className="w-full border-collapse text-sm rounded-lg overflow-hidden shadow-sm">
          <thead>
            <MarkdownTableRow line={headerLine} isHeader />
          </thead>
          <tbody>
            {bodyLines
              .filter(l => l.trim().startsWith('|'))
              .map((l, i) => <MarkdownTableRow key={i} line={l} isHeader={false} />)}
          </tbody>
        </table>
      </div>
    )
    tableLines = []
    inTable = false
  }

  lines.forEach((raw, i) => {
    const line = raw.trimEnd()

    // Table detection
    if (line.trim().startsWith('|')) {
      inTable = true
      tableLines.push(line)
      return
    }
    if (inTable) flushTable()

    // ## Section headers
    if (/^#{1,3} /.test(line)) {
      blocks.push(
        <h4 key={i} className="font-bold text-base text-blue-900 mt-5 mb-2 border-b border-blue-200 pb-1">
          {line.replace(/^#+\s*/, '')}
        </h4>
      )
      return
    }

    // Bullet / list items
    if (/^[-*â€¢] /.test(line.trim())) {
      // Bold inline: **text**
      const parts = line.trim().replace(/^[-*â€¢] /, '').split(/(\*\*[^*]+\*\*)/)
      blocks.push(
        <li key={i} className="ml-4 text-gray-800 text-sm mb-1 flex gap-2">
          <span className="text-blue-500 shrink-0 mt-0.5">â€¢</span>
          <span>
            {parts.map((p, j) =>
              /^\*\*/.test(p)
                ? <strong key={j}>{p.replace(/\*\*/g, '')}</strong>
                : p
            )}
          </span>
        </li>
      )
      return
    }

    // Blank line â†’ spacing
    if (!line.trim()) {
      blocks.push(<div key={i} className="h-2" />)
      return
    }

    // Separator lines (---|---|---)
    if (/^[-|:]+$/.test(line.replace(/\s/g, ''))) return

    // Regular paragraph
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    blocks.push(
      <p key={i} className="text-gray-800 text-sm leading-relaxed mb-1">
        {parts.map((p, j) =>
          /^\*\*/.test(p)
            ? <strong key={j}>{p.replace(/\*\*/g, '')}</strong>
            : p
        )}
      </p>
    )
  })

  if (inTable) flushTable()

  return <div className="space-y-0.5">{blocks}</div>
}

// â”€â”€â”€ Main Component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function QueryForm() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')
  const [charts, setCharts] = useState([])
  const [sources, setSources] = useState([])
  const [confidence, setConfidence] = useState('')
  const [confidenceReason, setConfidenceReason] = useState('')
  const [intent, setIntent] = useState('')
  const [loading, setLoading] = useState(false)
  const [enableVisualization, setEnableVisualization] = useState(true)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setCharts([])
    setSources([])
    setConfidence('')
    setConfidenceReason('')
    setIntent('')

    try {
      const endpointPath = enableVisualization ? '/api/query-with-charts' : '/api/query'
      const requestCandidates = [
        `${PRIMARY_API_BASE}${endpointPath}`,
        `${FALLBACK_API_BASE}${endpointPath}`,
      ]
      const visualFallbackCandidates = enableVisualization
        ? [
            `${PRIMARY_API_BASE}/api/query`,
            `${FALLBACK_API_BASE}/api/query`,
          ]
        : []

      let res = null
      let lastError = null

      const postToCandidates = async (candidates) => {
        for (const url of candidates) {
          try {
            return await axios.post(url, { query }, { timeout: 15000 })
          } catch (err) {
            lastError = err
          }
        }
        return null
      }

      res = await postToCandidates(requestCandidates)

      if (!res && enableVisualization) {
        // Chart endpoint might be absent; fallback to base query endpoint.
        res = await postToCandidates(visualFallbackCandidates)
      }

      if (!res) {
        throw lastError || new Error('Unable to reach backend query endpoint.')
      }

      // Both endpoints now return a consistent shape
      const data = res.data
      setResponse(data.response || data.text || '')
      if (data.sources)    setSources(data.sources)
      if (data.confidence) setConfidence(data.confidence)
      if (data.confidence_reason) setConfidenceReason(data.confidence_reason)
      if (data.intent || data.query_type) setIntent(data.intent || data.query_type)
      if (data.charts?.length) setCharts(data.charts)

    } catch (error) {
      const status = error?.response?.status
      const serverMsg = error?.response?.data?.error || error?.response?.data?.message
      if (error?.code === 'ECONNABORTED' || error?.message === 'Network Error') {
        setResponse('Error: Backend is unreachable from browser. Ensure backend is running on port 4000 and try again.')
      } else if (status === 404) {
        setResponse('Error: Query endpoint is unavailable on the current backend instance. Restart backend on port 4000 and try again.')
      } else {
        setResponse('Error: ' + (serverMsg || error.message))
      }
      setCharts([])
      setSources([])
      setConfidence('')
      setConfidenceReason('')
      setIntent('')
    }
    setLoading(false)
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="mb-3">
          <label className="flex items-center space-x-2 text-sm text-gray-700 mb-2">
            <input
              type="checkbox"
              checked={enableVisualization}
              onChange={(e) => setEnableVisualization(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="font-medium">Enable chart visualization for comparison queries</span>
          </label>
        </div>

        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Ask a question about your documents...

Examples:
â€¢ Compare India's growth with and without port construction by 2030
â€¢ Forecast India EV sales by 2040
â€¢ What is the impact of EV infrastructure on market growth?
â€¢ Analyze policy differences between China and India`}
          className="w-full p-3 border border-gray-300 rounded-lg mb-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={6}
        />

        <button
          type="submit"
          disabled={loading}
          className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-6 py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing...
            </span>
          ) : (
            'Submit Query'
          )}
        </button>
      </form>

      {response && (
        <div className="space-y-4">

          {/* Confidence + Intent badges */}
          {(confidence || intent) && (
            <div className={`border-l-4 p-4 rounded flex flex-wrap items-center gap-3 ${
              confidence === 'High'   ? 'border-green-500 bg-green-50' :
              confidence === 'Medium' ? 'border-yellow-500 bg-yellow-50' :
              'border-red-500 bg-red-50'
            }`}>
              {confidence && (
                <div className="flex flex-col gap-0.5">
                  <span className="flex items-center gap-1.5">
                    <span className="font-semibold text-gray-700">Confidence:</span>
                    <span className={`font-bold ${
                      confidence === 'High'   ? 'text-green-700' :
                      confidence === 'Medium' ? 'text-yellow-700' :
                      'text-red-700'
                    }`}>{confidence}</span>
                  </span>
                  {confidenceReason && (
                    <span className={`text-xs italic ${
                      confidence === 'High'   ? 'text-green-600' :
                      confidence === 'Medium' ? 'text-yellow-600' :
                      'text-red-500'
                    }`}>{confidenceReason}</span>
                  )}
                </div>
              )}
              {intent && INTENT_META[intent] && (
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${INTENT_META[intent].color}`}>
                  {INTENT_META[intent].label} Query
                </span>
              )}
              {sources.length > 0 && (
                <span className="text-sm text-gray-600 ml-auto">
                  {sources.length} source{sources.length !== 1 ? 's' : ''} retrieved
                </span>
              )}
            </div>
          )}

          {/* Structured response */}
          <div className="border border-gray-200 rounded-xl bg-white shadow-sm overflow-hidden">
            <div className="bg-gradient-to-r from-gray-50 to-white px-5 py-3 border-b border-gray-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-green-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-bold text-gray-800">Analysis</span>
            </div>
            <div className="p-5">
              <StructuredResponse text={response} />
            </div>
          </div>

          {/* Sources */}
          {sources.length > 0 && (
            <div className="border border-blue-200 p-5 rounded-xl bg-blue-50">
              <h3 className="font-bold text-base mb-3 text-blue-900 flex items-center gap-2">
                <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Sources Used
              </h3>
              <div className="space-y-2">
                {sources.map((source, index) => (
                  <div key={index} className="bg-white p-3 rounded border border-blue-200">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <span className="bg-blue-600 text-white text-xs font-bold px-2 py-0.5 rounded">
                          {source.source_id}
                        </span>
                        <span className="font-medium text-gray-800 text-sm">{source.filename}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          source.document_type === 'Excel'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-purple-100 text-purple-800'
                        }`}>
                          {source.document_type}
                        </span>
                        <span className="text-xs text-gray-500">
                          {(source.similarity_score * 100).toFixed(1)}% match
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Charts */}
          <ChartDisplay charts={charts} />
        </div>
      )}
    </div>
  )
}