import React, { useState } from 'react';
import ForecastVisualization from './ForecastVisualization';
import PolicyInsights from './PolicyInsights';
import PolicySimulator from './PolicySimulator';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:4000';
const UPLOAD_URL = `${API_BASE_URL}/api/upload`;
const UPLOAD_FORECAST_URL = `${API_BASE_URL}/api/upload-and-forecast`;

// Add custom animations
const styles = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .animate-fadeIn {
    animation: fadeIn 0.5s ease-out forwards;
  }

  .animate-slideIn {
    animation: slideIn 0.6s ease-out forwards;
  }
`;

export default function SmartUploadForecast() {
  const [files, setFiles] = useState([]);
  const [forecastTarget, setForecastTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [baseForecastData, setBaseForecastData] = useState([]);
  const [forecastPeriods, setForecastPeriods] = useState(36);
  const [healthChecking, setHealthChecking] = useState(false);
  const [backendHealth, setBackendHealth] = useState({
    status: 'unknown',
    message: 'Not checked yet',
    checkedAt: null,
  });

  const parseJsonSafely = async (response) => {
    try {
      return await response.json();
    } catch {
      return {};
    }
  };

  const checkBackendHealth = async () => {
    setHealthChecking(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`, { method: 'GET' });
      const data = await parseJsonSafely(response);

      if (response.ok) {
        setBackendHealth({
          status: 'online',
          message: data?.status ? `Backend ${data.status}` : 'Backend reachable',
          checkedAt: new Date(),
        });
      } else {
        setBackendHealth({
          status: 'offline',
          message: `Health check failed (${response.status})`,
          checkedAt: new Date(),
        });
      }
    } catch (_err) {
      setBackendHealth({
        status: 'offline',
        message: `Cannot reach ${API_BASE_URL}`,
        checkedAt: new Date(),
      });
    } finally {
      setHealthChecking(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files || []);
    if (!selected.length) return;

    const valid = selected.filter((f) => f.name.endsWith('.pdf') || f.name.endsWith('.xlsx') || f.name.endsWith('.xls') || f.name.endsWith('.csv'));
    if (!valid.length) {
      setError('Please select PDF, Excel, or CSV files');
      return;
    }

    if (valid.length !== selected.length) {
      setError('Some files were skipped (only PDF/XLSX/XLS/CSV allowed)');
    } else {
      setError(null);
    }

    // Append to existing files instead of replacing
    setFiles((prev) => [...prev, ...valid]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setFiles([]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!files.length) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));

    try {
      const response = await fetch(UPLOAD_URL, {
        method: 'POST',
        body: formData,
      });

      const data = await parseJsonSafely(response);
      if (response.ok) {
        setUploadedFiles(files.map(f => ({ name: f.name, size: f.size })));
        setError(null);
      } else {
        setError(data.error || `Upload failed (${response.status})`);
      }
    } catch (err) {
      // Detailed error analysis for better debugging
      const errMsg = String(err?.message || '').toLowerCase();
      let errorText = '';
      
      if (errMsg.includes('failed to fetch')) {
        errorText = `Network/CORS Error: Cannot reach ${UPLOAD_URL}\n\n` +
          `✓ Ensure backend is running: python run.py in backend folder\n` +
          `✓ Check backend is on port 4000\n` +
          `✓ Check CORS allows localhost:3000\n` +
          `✓ Check firewall/antivirus blocks port 4000`;
      } else if (errMsg.includes('abort')) {
        errorText = `Request Timeout: Backend took too long to respond`;
      } else {
        errorText = `Error: ${err.message}`;
      }
      
      setError(errorText);
    } finally {
      setUploading(false);
    }
  };

  const handleForecast = async (e) => {
    e.preventDefault();
    if (!files.length) {
      setError('Please upload files first');
      return;
    }

    if (!forecastTarget.trim()) {
      setError('Please describe what you want to forecast');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    files.forEach((f) => formData.append('files[]', f));
    formData.append('forecast_periods', forecastPeriods);
    formData.append('auto_select', 'true');
    formData.append('forecast_target', forecastTarget.trim());

    try {
      const response = await fetch(UPLOAD_FORECAST_URL, {
        method: 'POST',
        body: formData,
      });

      const data = await parseJsonSafely(response);
      if (response.ok) {
        setResults(data);

        // Extract forecast data for policy simulator
        if (data.forecasts && data.forecasts.length > 0) {
          const firstForecast = data.forecasts[0];
          if (firstForecast.models_comparison?.ensemble?.forecast_data) {
            setBaseForecastData(firstForecast.models_comparison.ensemble.forecast_data);
          }
        }
      } else {
        setError(data.error || `Forecast failed (${response.status})`);
      }
    } catch (err) {
      const isFetchFailure = String(err?.message || '').toLowerCase().includes('failed to fetch');
      setError(
        isFetchFailure
          ? `Network/CORS error: cannot reach ${UPLOAD_FORECAST_URL}. Ensure backend is running and CORS allows http://localhost:3000.`
          : `Error: ${err.message}`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Enhanced Header */}
        <div className="mb-8 text-center">
          <div className="inline-block p-4 bg-white rounded-full shadow-lg mb-4">
            <span className="text-6xl">📊</span>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
            Smart Document Upload & ML Forecasting
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your data files, and let AI-powered forecasting models predict future trends with precision.
          </p>

          {/* Progress Indicator */}
          <div className="mt-6 flex items-center justify-center space-x-4">
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${files.length > 0 || uploadedFiles.length > 0 ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'} font-bold transition-all`}>
                1
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700">Upload</span>
            </div>
            <div className={`w-12 h-1 ${uploadedFiles.length > 0 ? 'bg-blue-600' : 'bg-gray-300'} transition-all`}></div>
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${uploadedFiles.length > 0 ? 'bg-green-600 text-white' : 'bg-gray-300 text-gray-600'} font-bold transition-all`}>
                2
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700">Forecast</span>
            </div>
            <div className={`w-12 h-1 ${results ? 'bg-green-600' : 'bg-gray-300'} transition-all`}></div>
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${results ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-600'} font-bold transition-all`}>
                3
              </div>
              <span className="ml-2 text-sm font-medium text-gray-700">Results</span>
            </div>
          </div>
        </div>

        {/* Step 1: Upload Documents */}
        <div className="bg-white rounded-xl shadow-xl p-8 mb-8 border border-gray-100 hover:shadow-2xl transition-shadow">
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-2xl">📤</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-800">Step 1: Upload Documents</h2>
          </div>
          <form onSubmit={handleUpload}>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Documents (PDF, XLSX, XLS, CSV)
              </label>
              <input
                type="file"
                multiple
                onChange={handleFileChange}
                accept=".pdf,.xlsx,.xls,.csv"
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100"
              />

              {/* Selected files list with remove buttons */}
              {files.length > 0 && (
                <div className="mt-4 bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-sm font-semibold text-gray-700">
                      Selected Files ({files.length})
                    </p>
                    <button
                      type="button"
                      onClick={clearAllFiles}
                      className="text-xs text-red-600 hover:text-red-800 font-semibold"
                    >
                      Clear All
                    </button>
                  </div>
                  <ul className="space-y-2">
                    {files.map((file, index) => (
                      <li key={index} className="flex justify-between items-center bg-white px-3 py-2 rounded border border-gray-200">
                        <span className="text-sm text-gray-800 truncate flex-1">
                          📄 {file.name} <span className="text-gray-500">({(file.size / 1024).toFixed(1)} KB)</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="ml-2 text-red-500 hover:text-red-700 text-xs font-bold"
                        >
                          ✕
                        </button>
                      </li>
                    ))}
                  </ul>

                  {/* Add more files button */}
                  <label className="mt-3 inline-block cursor-pointer bg-green-50 hover:bg-green-100 text-green-700 px-4 py-2 rounded text-sm font-semibold transition">
                    + Add More Files
                    <input
                      type="file"
                      multiple
                      onChange={handleFileChange}
                      accept=".pdf,.xlsx,.xls,.csv"
                      className="hidden"
                    />
                  </label>
                </div>
              )}
            </div>

            <div className="mb-5 rounded-lg border border-blue-200 bg-blue-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-semibold text-gray-700">Backend Status:</span>
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-semibold ${
                      backendHealth.status === 'online'
                        ? 'bg-green-100 text-green-800'
                        : backendHealth.status === 'offline'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {backendHealth.status.toUpperCase()}
                  </span>
                  <span className="text-gray-600">{backendHealth.message}</span>
                </div>
                <button
                  type="button"
                  onClick={checkBackendHealth}
                  disabled={healthChecking}
                  className="rounded-md bg-white px-3 py-2 text-xs font-semibold text-blue-700 shadow-sm ring-1 ring-blue-200 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {healthChecking ? 'Checking...' : 'Check Backend'}
                </button>
              </div>
              {backendHealth.checkedAt && (
                <p className="mt-2 text-xs text-gray-500">
                  Last checked: {backendHealth.checkedAt.toLocaleTimeString()}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={uploading || !files.length}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-400 text-white font-bold py-4 rounded-lg transition-all transform hover:scale-105 disabled:hover:scale-100 shadow-lg disabled:shadow-none"
            >
              {uploading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading to Vector Database...
                </span>
              ) : (
                '📤 Upload Documents to Database'
              )}
            </button>
          </form>

          {/* Show uploaded files confirmation with animation */}
          {uploadedFiles.length > 0 && !results && (
            <div className="mt-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-5 shadow-md animate-slideIn">
              <div className="flex items-center mb-3">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-2">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-green-800">Documents Uploaded & Indexed Successfully!</h3>
              </div>
              <ul className="space-y-2">
                {uploadedFiles.map((file, index) => (
                  <li key={index} className="flex items-center text-sm text-gray-700 bg-white rounded-lg p-2 border border-green-200">
                    <span className="mr-2 text-green-600">✓</span>
                    <span className="font-medium">📄 {file.name}</span>
                    <span className="ml-auto text-gray-500">({(file.size / 1024).toFixed(1)} KB)</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-sm text-green-700 font-medium">
                🎯 Ready for forecasting! Proceed to Step 2 below.
              </p>
            </div>
          )}
        </div>

        {/* Step 2: Forecast Query (shown ONLY after successful upload to database) */}
        {uploadedFiles.length > 0 && !results && (
          <div className="bg-white rounded-xl shadow-xl p-8 mb-8 border-2 border-green-200 hover:shadow-2xl transition-all animate-fadeIn">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center mr-3 shadow-lg">
                <span className="text-3xl">🔮</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Step 2: What Should We Forecast?</h2>
            </div>
            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 mb-6 border border-green-200">
              <p className="text-sm text-gray-700 leading-relaxed">
                ✅ <strong>Your documents have been uploaded and indexed in the vector database.</strong><br/>
                Now ask what you'd like to forecast from the data, and our AI models will analyze and predict future trends.
              </p>
            </div>
            <form onSubmit={handleForecast}>
              <div className="mb-6">
                <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <span className="mr-2">🎯</span>
                  What would you like to forecast?
                </label>
                <input
                  type="text"
                  value={forecastTarget}
                  onChange={(e) => setForecastTarget(e.target.value)}
                  placeholder="e.g., EV sales, revenue, units shipped, market growth"
                  className="w-full px-5 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all text-lg"
                />
                <p className="text-xs text-gray-500 mt-2 ml-1">💡 We'll automatically find and analyze the best matching data series from your documents.</p>
              </div>

              <div className="mb-6">
                <label className="flex items-center text-sm font-semibold text-gray-700 mb-3">
                  <span className="mr-2">📅</span>
                  How many months ahead should we forecast?
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={forecastPeriods}
                    onChange={(e) => setForecastPeriods(parseInt(e.target.value))}
                    min="3"
                    max="120"
                    className="w-full px-5 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all text-lg"
                  />
                  <span className="absolute right-4 top-3 text-gray-400 font-medium">months</span>
                </div>
                <p className="text-xs text-gray-500 mt-2 ml-1">⚙️ Recommended: 36 months (3 years) for optimal predictions</p>
              </div>

              <button
                type="submit"
                disabled={loading || !files.length || !forecastTarget.trim()}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-bold py-4 rounded-xl transition-all transform hover:scale-105 disabled:hover:scale-100 shadow-xl disabled:shadow-none"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Training AI Models & Generating Forecast...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <span className="mr-2">🚀</span>
                    Generate AI-Powered Forecast
                  </span>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Enhanced Error Display */}
        {error && (
          <div className="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 text-red-800 px-6 py-4 rounded-xl mb-8 shadow-lg animate-slideIn">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center mr-3">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div>
                <p className="font-bold text-lg">Oops! Something went wrong</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results Display */}
        {results && (
          <div className="space-y-6">
            {/* Summary */}
            {results.summary && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h2 className="text-xl font-bold text-green-800 mb-4">✅ Processing Complete</h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-3xl font-bold text-green-600">{results.summary.files_processed || 0}</p>
                    <p className="text-gray-700">Files Processed</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-blue-600">{results.summary.files_with_forecasts || 0}</p>
                    <p className="text-gray-700">With Forecasts</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-purple-600">{results.summary.total_models_trained || 0}</p>
                    <p className="text-gray-700">Models Trained</p>
                  </div>
                </div>
              </div>
            )}

            {/* Document Information */}
            {results.documents && Array.isArray(results.documents) && results.documents.map((doc, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-2">{doc.filename}</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Status: <span className={doc.status === 'success' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                    {doc.status.toUpperCase()}
                  </span>
                </p>
                
                {doc.extraction && (
                  <div className="bg-gray-50 p-4 rounded text-sm">
                    <p className="font-semibold text-gray-700 mb-2">Extraction Details:</p>
                    {doc.extraction.sheets && doc.extraction.sheets.length > 0 && (
                      <p>📋 Sheets: {doc.extraction.sheets.join(', ')}</p>
                    )}
                    {doc.extraction.time_series_candidates && doc.extraction.time_series_candidates.length > 0 && (
                      <p>📈 Time Series Found: {doc.extraction.time_series_candidates.length}</p>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Forecast Results */}
            {results.forecasts && Array.isArray(results.forecasts) && results.forecasts.map((forecast, idx) => (
              <div key={idx} className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-indigo-900 mb-4">📊 Forecast Results - {forecast.filename}</h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
                  <div className="bg-white p-4 rounded">
                    <p className="text-gray-600 text-sm">Data Series</p>
                    <p className="font-semibold text-gray-800">{forecast.data_series}</p>
                  </div>
                  <div className="bg-white p-4 rounded">
                    <p className="text-gray-600 text-sm">Historical Points</p>
                    <p className="font-semibold text-gray-800">{forecast.data_points}</p>
                  </div>
                  <div className="bg-white p-4 rounded">
                    <p className="text-gray-600 text-sm">Best Model</p>
                    <p className="font-semibold text-blue-600">{forecast.best_model}</p>
                  </div>
                  <div className="bg-white p-4 rounded">
                    <p className="text-gray-600 text-sm">R² Score</p>
                    <p className="font-semibold text-green-600">{forecast.best_r2_score}</p>
                  </div>
                </div>

                {/* Model Comparison - Simplified */}
                <div className="bg-white p-4 rounded">
                  <p className="font-semibold text-gray-800 mb-3">🏆 Best Forecasting Model Selected:</p>
                  <p className="text-lg font-bold text-blue-600 mb-2">{forecast.best_model}</p>
                  <p className="text-sm text-gray-600">This model provides the most accurate predictions for your data based on R² score analysis.</p>
                </div>
              </div>
            ))}
            
            {/* Add Forecast Visualizations */}
            {results.forecasts && <ForecastVisualization forecasts={results.forecasts} />}
            
            {/* Add Policy Simulator */}
            <PolicySimulator baseForecast={baseForecastData} />
            
            {/* Add Policy Insights */}
            {results.policy_insights && results.policy_charts && (
              <PolicyInsights
                policyData={results.policy_insights}
                policyCharts={results.policy_charts}
              />
            )}
          </div>
        )}
      </div>
    </div>
    </>
  );
}