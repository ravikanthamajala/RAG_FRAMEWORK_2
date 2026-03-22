import { useState, useEffect } from 'react'
import ForecastInsights from './ForecastInsights'

const SummaryCard = ({ title, value, subtitle, icon }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-600 text-sm font-semibold">{title}</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{value}</p>
          {subtitle && <p className="text-sm text-green-600 mt-1">{subtitle}</p>}
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  )
}

const ForecastLineChart = ({ data, title, xLabel, yLabel }) => {
  const [tooltip, setTooltip] = useState(null)

  if (!data || data.length === 0) return null

  const yValues = data.map(d => d.y)
  const minY = Math.min(...yValues)
  const maxY = Math.max(...yValues)

  // Generously sized canvas so labels have room
  const W = 920
  const H = 500
  const pLeft = 100   // room for y-axis value labels
  const pRight = 30
  const pTop = 50
  const pBottom = 90  // room for x-axis labels + label text

  const plotW = W - pLeft - pRight
  const plotH = H - pTop - pBottom

  const scaleX = plotW / (data.length - 1 || 1)
  const scaleY = plotH / (maxY - minY || 1)

  const px = (idx) => pLeft + idx * scaleX
  const py = (val) => pTop + plotH - (val - minY) * scaleY

  // Build line path and closed area path
  const linePath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${px(i)} ${py(d.y)}`).join(' ')
  const areaPath = [
    `M ${px(0)} ${pTop + plotH}`,
    ...data.map((d, i) => `L ${px(i)} ${py(d.y)}`),
    `L ${px(data.length - 1)} ${pTop + plotH}`,
    'Z',
  ].join(' ')

  // 6 horizontal grid lines
  const gridSteps = 5
  const yTicks = Array.from({ length: gridSteps + 1 }, (_, i) => {
    const frac = i / gridSteps
    return { y: pTop + frac * plotH, value: maxY - frac * (maxY - minY) }
  })

  return (
    <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
      <h3 className="font-bold text-2xl text-center mb-4 text-gray-800">{title}</h3>
      <div className="w-full overflow-x-auto">
        <svg
          width="100%"
          height={H}
          viewBox={`0 0 ${W} ${H}`}
          style={{ minWidth: '340px', display: 'block' }}
        >
          <defs>
            <linearGradient id="lineAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Plot background */}
          <rect x={pLeft} y={pTop} width={plotW} height={plotH} fill="#f8faff" rx="4" />

          {/* Horizontal grid lines + Y-axis tick labels */}
          {yTicks.map((tick, i) => (
            <g key={`ytick-${i}`}>
              <line
                x1={pLeft} y1={tick.y}
                x2={pLeft + plotW} y2={tick.y}
                stroke={i === gridSteps ? '#94a3b8' : '#e2e8f0'}
                strokeWidth={i === gridSteps ? 2 : 1}
                strokeDasharray={i === gridSteps ? '0' : '5,4'}
              />
              <text
                x={pLeft - 10}
                y={tick.y + 5}
                fontSize="13"
                fill="#64748b"
                textAnchor="end"
                fontFamily="system-ui, sans-serif"
              >
                {tick.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </text>
            </g>
          ))}

          {/* Y-axis line */}
          <line x1={pLeft} y1={pTop} x2={pLeft} y2={pTop + plotH} stroke="#94a3b8" strokeWidth="2" />

          {/* Area fill */}
          <path d={areaPath} fill="url(#lineAreaGrad)" />

          {/* Main line */}
          <path
            d={linePath}
            fill="none"
            stroke="#2563eb"
            strokeWidth="3.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Data points + invisible hit areas + x-labels */}
          {data.map((point, idx) => {
            const cx = px(idx)
            const cy = py(point.y)
            const isHovered = tooltip?.idx === idx
            return (
              <g key={idx}>
                {/* X-axis label */}
                <text
                  x={cx}
                  y={pTop + plotH + 28}
                  fontSize="14"
                  textAnchor="middle"
                  fill="#374151"
                  fontWeight="600"
                  fontFamily="system-ui, sans-serif"
                >
                  {point.x}
                </text>

                {/* Hover glow */}
                {isHovered && <circle cx={cx} cy={cy} r="16" fill="#2563eb" opacity="0.12" />}

                {/* Data point */}
                <circle
                  cx={cx} cy={cy}
                  r={isHovered ? 8 : 6}
                  fill={isHovered ? '#1d4ed8' : '#2563eb'}
                  stroke="white"
                  strokeWidth="2.5"
                />

                {/* Value label above point */}
                <text
                  x={cx}
                  y={cy - 14}
                  fontSize="12"
                  textAnchor="middle"
                  fill="#1e40af"
                  fontWeight="700"
                  fontFamily="system-ui, sans-serif"
                >
                  {point.y.toLocaleString()}
                </text>

                {/* Wide invisible hover zone */}
                <rect
                  x={cx - (scaleX / 2)}
                  y={pTop}
                  width={scaleX}
                  height={plotH}
                  fill="transparent"
                  style={{ cursor: 'crosshair' }}
                  onMouseEnter={() => setTooltip({ idx, cx, cy, point })}
                  onMouseLeave={() => setTooltip(null)}
                />
              </g>
            )
          })}

          {/* SVG tooltip box */}
          {tooltip && (() => {
            const tx = Math.min(tooltip.cx + 16, W - 170)
            const ty = Math.max(tooltip.cy - 60, pTop)
            return (
              <g>
                <rect x={tx} y={ty} width={155} height={56} rx="7" fill="#1e3a8a" opacity="0.93" />
                <text x={tx + 12} y={ty + 20} fontSize="12" fill="#93c5fd" fontFamily="system-ui, sans-serif">
                  Year: {tooltip.point.x}
                </text>
                <text x={tx + 12} y={ty + 40} fontSize="13" fill="white" fontWeight="bold" fontFamily="system-ui, sans-serif">
                  {tooltip.point.y.toLocaleString()} units
                </text>
              </g>
            )
          })()}

          {/* Y-axis label (rotated) */}
          <text
            transform={`rotate(-90)`}
            x={-(pTop + plotH / 2)}
            y={22}
            fontSize="14"
            fill="#4b5563"
            fontWeight="700"
            textAnchor="middle"
            fontFamily="system-ui, sans-serif"
          >
            {yLabel}
          </text>

          {/* X-axis label */}
          <text
            x={pLeft + plotW / 2}
            y={H - 8}
            fontSize="14"
            textAnchor="middle"
            fill="#4b5563"
            fontWeight="700"
            fontFamily="system-ui, sans-serif"
          >
            {xLabel}
          </text>
        </svg>
      </div>
    </div>
  )
}

const selectBestForecast = (forecasts) => {
  if (!forecasts || forecasts.length === 0) return null

  const byMatch = forecasts
    .filter(f => typeof f.match_score === 'number')
    .sort((a, b) => b.match_score - a.match_score)

  if (byMatch.length > 0) return byMatch[0]

  const keywordPriority = ['car', 'sales', 'india']
  const scored = forecasts.map(f => {
    const haystack = `${f.filename || ''} ${f.data_series || ''}`.toLowerCase()
    const score = keywordPriority.reduce((acc, kw) => acc + (haystack.includes(kw) ? 1 : 0), 0)
    return { forecast: f, score }
  }).sort((a, b) => b.score - a.score)

  return scored[0]?.forecast || forecasts[0]
}

const DataQualityBadge = ({ quality }) => {
  if (!quality) return null
  
  const score = quality.quality_score || 0
  const color = score > 0.7 ? 'green' : score > 0.4 ? 'yellow' : 'red'
  const bgColor = color === 'green' ? 'bg-green-100' : color === 'yellow' ? 'bg-yellow-100' : 'bg-red-100'
  const textColor = color === 'green' ? 'text-green-800' : color === 'yellow' ? 'text-yellow-800' : 'text-red-800'
  
  return (
    <div className={`${bgColor} ${textColor} px-3 py-2 rounded-lg text-sm font-semibold inline-block`}>
      Data Quality: {(score * 100).toFixed(0)}%
      {quality.trend_direction && <span className="ml-2">({quality.trend_direction})</span>}
    </div>
  )
}

const buildYearlyFromForecast = (forecastArray) => {
  const records = Array.isArray(forecastArray) ? forecastArray : []
  
  // Check if using new Pydantic format (has 'period' field)
  const hasPeriods = records.some(r => typeof r === 'object' && 'period' in r)
  
  if (hasPeriods) {
    // Group by year from period (assuming monthly or daily)
    const yearly = {}
    records.forEach((r, idx) => {
      const period = r.period || idx + 1
      const value = r.forecast ?? r.yhat ?? r.value ?? 0
      
      // Estimate year from period (12 months per year)
      const yearOffset = Math.floor(period / 12)
      const year = 2025 + yearOffset
      
      if (!yearly[year]) yearly[year] = []
      yearly[year].push(Number(value) || 0)
    })
    
    return Object.keys(yearly)
      .sort()
      .map(year => {
        const values = yearly[year]
        const avgValue = values.reduce((a, b) => a + b, 0) / Math.max(values.length, 1)
        return { x: year, y: Math.round(Math.max(0, avgValue)) }
      })
  }
  
  // Check for date-based format
  const hasDates = records.some(r => typeof r === 'object' && r.ds)

  if (hasDates) {
    const yearly = {}
    records.forEach(r => {
      const dt = new Date(r.ds)
      if (Number.isNaN(dt.getTime())) return
      const year = dt.getFullYear()
      const value = r.yhat ?? r.forecast ?? r.value ?? 0
      if (!yearly[year]) yearly[year] = []
      yearly[year].push(Number(value) || 0)
    })

    return Object.keys(yearly)
      .sort()
      .map(year => {
        const values = yearly[year]
        const avgValue = values.reduce((a, b) => a + b, 0) / Math.max(values.length, 1)
        return { x: year, y: Math.round(Math.max(0, avgValue)) }
      })
  }

  // Fallback: assume monthly data
  const years = ['2025', '2026', '2027', '2028', '2029', '2030']
  const monthsPerYear = 12

  return years.map((year, yearIdx) => {
    const startIdx = yearIdx * monthsPerYear
    const endIdx = Math.min(startIdx + monthsPerYear, records.length)
    const yearMonths = records.slice(startIdx, endIdx)

    const values = yearMonths.map(m => {
      if (typeof m === 'object') {
        return m.forecast || m.yhat || m.value || 0
      }
      return m
    })

    const avgValue = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0
    return { x: year, y: Math.round(Math.max(0, avgValue)) }
  })
}

export default function ForecastVisualization({ forecasts }) {
  const [chartData, setChartData] = useState(null)
  const [summary, setSummary] = useState(null)
  const [dataQuality, setDataQuality] = useState(null)
  const [ensembleInfo, setEnsembleInfo] = useState(null)

  useEffect(() => {
    if (!forecasts || forecasts.length === 0) return

    // Select the most relevant forecast (car sales / India)
    const forecast = selectBestForecast(forecasts)
    if (!forecast) return

    console.log('Processing forecast:', forecast)
    
    let forecastData = null
    
    // Try multiple paths for ensemble forecast data
    if (forecast.models_comparison?.ensemble?.forecast_data) {
      forecastData = forecast.models_comparison.ensemble.forecast_data
      setEnsembleInfo({
        bestModel: forecast.models_comparison.ensemble.best_model,
        weights: forecast.models_comparison.ensemble.weights
      })
    } else if (forecast.models_comparison?.comparison) {
      // Fallback to best model
      const bestModel = forecast.models_comparison.comparison[forecast.best_model?.toLowerCase()]
      if (bestModel?.forecast_data) {
        forecastData = bestModel.forecast_data
      }
    }

    // If still no data, try direct forecast_data field
    if (!forecastData && forecast.forecast_data) {
      forecastData = forecast.forecast_data
    }

    // Extract forecast values
    let forecastArray = []
    if (Array.isArray(forecastData)) {
      forecastArray = forecastData
    } else if (typeof forecastData === 'object' && forecastData !== null) {
      forecastArray = Object.values(forecastData)
    }

    console.log('Extracted forecast array:', forecastArray)

    if (forecastArray.length === 0) {
      console.warn('No forecast data found in any expected location')
      return
    }

    const yearlyData = buildYearlyFromForecast(forecastArray)
    setChartData(yearlyData)

    // Set data quality
    if (forecast.data_quality) {
      setDataQuality(forecast.data_quality)
    }

    // Calculate summary
    const totalSales = yearlyData.reduce((sum, d) => sum + d.y, 0)
    const avgSales = Math.round(totalSales / yearlyData.length)
    const growthRate = yearlyData.length > 1
      ? (((yearlyData[yearlyData.length - 1].y - yearlyData[0].y) / Math.max(yearlyData[0].y, 1)) * 100).toFixed(1)
      : 0

    setSummary({
      totalSales: totalSales.toLocaleString(),
      avgSales: avgSales.toLocaleString(),
      growthRate: growthRate,
      dataPoints: forecast.data_points,
      series: forecast.data_series,
      r2Score: forecast.best_r2_score
    })
  }, [forecasts])

  if (!chartData || !summary) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-yellow-800">
        <p className="font-semibold">⚠️ Forecast Data Not Available</p>
        <p className="text-sm mt-2">The system is processing your forecast but chart data is not yet ready. Please refresh the page or try uploading again.</p>
        {forecasts && forecasts.length > 0 && (
          <details className="mt-4 text-xs cursor-pointer">
            <summary>Technical Details</summary>
            <pre className="bg-white p-2 rounded mt-2 overflow-auto max-h-48 text-gray-700">
              {JSON.stringify(forecasts[0], null, 2)}
            </pre>
          </details>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {dataQuality && (
        <div className="flex justify-between items-center">
          <DataQualityBadge quality={dataQuality} />
          {ensembleInfo && (
            <div className="text-sm text-gray-600">
              <span className="font-semibold">Best Model:</span> {ensembleInfo.bestModel}
              {ensembleInfo.weights && (
                <span className="ml-2">
                  (Weights: {Object.entries(ensembleInfo.weights).map(([k, v]) => `${k}: ${(v * 100).toFixed(0)}%`).join(', ')})
                </span>
              )}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Projected Sales (2025-2030)"
          value={summary.totalSales}
          subtitle="Units"
          icon="📊"
        />
        <SummaryCard
          title="Average Annual Sales"
          value={summary.avgSales}
          subtitle="Units/Year"
          icon="📈"
        />
        <SummaryCard
          title="Growth Rate"
          value={`${summary.growthRate}%`}
          subtitle="2025 to 2030"
          icon="🚀"
        />
        <SummaryCard
          title="Model Accuracy (R²)"
          value={summary.r2Score !== undefined ? summary.r2Score.toFixed(3) : 'N/A'}
          subtitle={`${summary.dataPoints} points`}
          icon="🎯"
        />
      </div>

      <ForecastLineChart
        data={chartData}
        title="🇮🇳 India Car Sales Forecast 2025-2030"
        xLabel="Year"
        yLabel="Car Sales Volume (Units)"
      />

      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
        <h4 className="font-bold text-blue-900 mb-2">📌 Key Insights</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>✓ Forecast shows India's automotive market projection from 2025 to 2030</li>
          <li>✓ Annual sales volumes are calculated from {summary.dataPoints} historical data points</li>
          <li>✓ Growth trajectory: {summary.growthRate}% CAGR over the forecast period</li>
          <li>✓ Based on analysis of: {summary.series}</li>
          {ensembleInfo && <li>✓ Using ensemble model combining: {Object.keys(ensembleInfo.weights).join(', ')}</li>}
          {dataQuality && dataQuality.seasonality_detected && <li>✓ Seasonal patterns detected in historical data</li>}
        </ul>
      </div>

      {/* Forecast Insights Q&A Component */}
      <ForecastInsights 
        forecastData={forecasts[0]} 
        forecastId={`forecast_${Date.now()}`}
      />
    </div>
  )
}
