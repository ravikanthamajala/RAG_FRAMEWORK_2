'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import Image from 'next/image';

interface ForecastReport {
  title: string;
  scenarios: any;
  policy_impact: any;
  key_findings: string[];
  recommendations: string[];
}

export default function Forecast2030() {
  const [report, setReport] = useState<ForecastReport | null>(null);
  const [charts, setCharts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchForecast = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get('http://localhost:4000/api/forecast/india-2030', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      setReport(response.data.report);
      setCharts(response.data.charts.chart_urls);
    } catch (err: any) {
      console.error('Forecast error:', err);
      setError(err.message || 'Failed to fetch forecast');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="inline-block">
          <div className="animate-spin h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
        <p className="mt-4 text-lg text-gray-600">Generating forecast with visualizations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-red-50 rounded-lg">
        <h2 className="text-xl font-bold text-red-800 mb-2">Error</h2>
        <p className="text-red-700">{error}</p>
        <button 
          onClick={fetchForecast}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!report) {
    return <div className="p-8 text-center text-gray-600">No data available</div>;
  }

  return (
    <div className="p-8 bg-gradient-to-b from-blue-50 to-white">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <h1 className="text-4xl font-bold mb-2 text-blue-900">{report.title}</h1>
        <p className="text-gray-600 mb-8">Comprehensive analysis of India's automotive market transformation by 2030</p>

        {/* Charts Section */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold mb-8 text-blue-800">Visualization Charts</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {charts.map((chart, idx) => (
              <div key={idx} className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition">
                <div className="w-full h-auto bg-gray-100 rounded">
                  <img 
                    src={`http://localhost:4000${chart}`} 
                    alt={`Chart ${idx + 1}`}
                    className="w-full h-auto object-contain"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Ctext x="50" y="50" text-anchor="middle" dy=".3em" fill="gray"%3EChart loading...%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Comparison Tables */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <div className="bg-gradient-to-br from-green-50 to-green-100 p-8 rounded-lg shadow-lg border-2 border-green-300">
            <h3 className="text-2xl font-bold mb-6 text-green-700 flex items-center">
              <span className="w-4 h-4 bg-green-500 rounded-full mr-3"></span>
              With China Policies (Aggressive)
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-green-300">
                <span className="font-semibold text-gray-700">2030 EV Units:</span>
                <span className="text-xl font-bold text-green-700">{report.scenarios.with_china_policies['2030_ev_units'].toFixed(2)}M</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-green-300">
                <span className="font-semibold text-gray-700">Market Share:</span>
                <span className="text-xl font-bold text-green-700">{report.scenarios.with_china_policies['2030_ev_percentage'].toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-green-300">
                <span className="font-semibold text-gray-700">Total Sales:</span>
                <span className="text-xl font-bold text-green-700">{report.scenarios.with_china_policies['2030_total_sales'].toFixed(2)}M</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-green-300">
                <span className="font-semibold text-gray-700">EV CAGR:</span>
                <span className="text-xl font-bold text-green-700">{report.scenarios.with_china_policies.cagr_ev.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="font-semibold text-gray-700">Cumulative EVs:</span>
                <span className="text-xl font-bold text-green-700">{report.scenarios.with_china_policies.cumulative_evs_2024_2030.toFixed(2)}M</span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-red-50 to-red-100 p-8 rounded-lg shadow-lg border-2 border-red-300">
            <h3 className="text-2xl font-bold mb-6 text-red-700 flex items-center">
              <span className="w-4 h-4 bg-red-500 rounded-full mr-3"></span>
              Without China Policies (BAU)
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-red-300">
                <span className="font-semibold text-gray-700">2030 EV Units:</span>
                <span className="text-xl font-bold text-red-700">{report.scenarios.without_china_policies['2030_ev_units'].toFixed(2)}M</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-red-300">
                <span className="font-semibold text-gray-700">Market Share:</span>
                <span className="text-xl font-bold text-red-700">{report.scenarios.without_china_policies['2030_ev_percentage'].toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-red-300">
                <span className="font-semibold text-gray-700">Total Sales:</span>
                <span className="text-xl font-bold text-red-700">{report.scenarios.without_china_policies['2030_total_sales'].toFixed(2)}M</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-red-300">
                <span className="font-semibold text-gray-700">EV CAGR:</span>
                <span className="text-xl font-bold text-red-700">{report.scenarios.without_china_policies.cagr_ev.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="font-semibold text-gray-700">Cumulative EVs:</span>
                <span className="text-xl font-bold text-red-700">{report.scenarios.without_china_policies.cumulative_evs_2024_2030.toFixed(2)}M</span>
              </div>
            </div>
          </div>
        </div>

        {/* Policy Impact Summary */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-700 text-white p-8 rounded-lg shadow-lg mb-12">
          <h3 className="text-2xl font-bold mb-6">Policy Impact Summary 📊</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-blue-600 p-6 rounded-lg">
              <p className="text-blue-100 text-sm mb-2">Additional EV Units (2030)</p>
              <p className="text-3xl font-bold">+{report.policy_impact.additional_ev_units_2030.toFixed(2)}M</p>
            </div>
            <div className="bg-blue-600 p-6 rounded-lg">
              <p className="text-blue-100 text-sm mb-2">Percentage Increase</p>
              <p className="text-3xl font-bold">+{report.policy_impact.percentage_increase.toFixed(1)}%</p>
            </div>
            <div className="bg-blue-600 p-6 rounded-lg">
              <p className="text-blue-100 text-sm mb-2">Market Share Gain</p>
              <p className="text-3xl font-bold">+{report.policy_impact.market_share_gain.toFixed(1)}%</p>
            </div>
            <div className="bg-blue-600 p-6 rounded-lg">
              <p className="text-blue-100 text-sm mb-2">Cumulative (2024-2030)</p>
              <p className="text-3xl font-bold">+{report.policy_impact.cumulative_additional_evs.toFixed(2)}M</p>
            </div>
          </div>
        </div>

        {/* Key Findings */}
        <div className="bg-white p-8 rounded-lg shadow-lg mb-12">
          <h3 className="text-2xl font-bold mb-6 text-gray-800">🔍 Key Findings</h3>
          <ul className="space-y-4">
            {report.key_findings.map((finding, idx) => (
              <li key={idx} className="flex items-start p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition">
                <span className="text-green-600 mr-4 font-bold text-xl flex-shrink-0">✓</span>
                <span className="text-gray-700">{finding}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div className="bg-white p-8 rounded-lg shadow-lg">
          <h3 className="text-2xl font-bold mb-6 text-gray-800">💡 Recommendations for India</h3>
          <ol className="space-y-4">
            {report.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start p-4 bg-amber-50 rounded-lg hover:bg-amber-100 transition">
                <span className="text-amber-600 mr-4 font-bold text-lg flex-shrink-0">{idx + 1}.</span>
                <span className="text-gray-700">{rec}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-gray-300 text-center text-gray-600">
          <p>Generated on {new Date().toLocaleDateString()} | India Automotive Market Analysis</p>
        </div>
      </div>
    </div>
  );
}
