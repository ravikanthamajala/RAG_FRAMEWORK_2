'use client';

import { useState } from 'react';
import axios from 'axios';

export default function ForecastInsights({ forecastData, forecastId }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer(null);

    try {
      const response = await axios.post('http://localhost:4000/api/forecast-insights/ask', {
        forecast_data: forecastData,
        question: question
      });

      setAnswer(response.data.result);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const exampleQuestions = [
    "What will be the market size in 2030?",
    "What is the average growth rate?",
    "When will we reach 30% market penetration?",
    "What are the key trends in this forecast?",
    "How reliable is this forecast?"
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
      <div className="mb-4">
        <h3 className="text-2xl font-bold text-gray-800 mb-2">
          🤔 Ask About This Forecast
        </h3>
        <p className="text-gray-600">
          Get insights and answers about the forecast results
        </p>
      </div>

      {/* Question Form */}
      <form onSubmit={handleAsk} className="mb-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Question
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about the forecast results..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows="3"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '🔄 Analyzing...' : '🚀 Get Answer'}
        </button>
      </form>

      {/* Example Questions */}
      <div className="mb-6">
        <p className="text-sm font-medium text-gray-700 mb-2">Example Questions:</p>
        <div className="space-y-2">
          {exampleQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => setQuestion(q)}
              className="block w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              💡 {q}
            </button>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">❌ {error}</p>
        </div>
      )}

      {/* Answer Display */}
      {answer && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 space-y-4">
          <div>
            <h4 className="text-lg font-semibold text-gray-800 mb-2">
              📊 Answer
            </h4>
            <p className="text-gray-700 whitespace-pre-wrap">{answer.answer}</p>
          </div>

          {answer.insights && answer.insights.length > 0 && (
            <div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                💡 Key Insights
              </h4>
              <ul className="space-y-2">
                {answer.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span className="text-gray-700">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {answer.forecast_summary && Object.keys(answer.forecast_summary).length > 0 && (
            <div className="grid grid-cols-2 gap-4 mt-4">
              {answer.forecast_summary.min_forecast && (
                <div className="bg-white rounded-lg p-3">
                  <p className="text-sm text-gray-600">Minimum Forecast</p>
                  <p className="text-xl font-bold text-gray-800">
                    {answer.forecast_summary.min_forecast.toLocaleString()}
                  </p>
                </div>
              )}
              {answer.forecast_summary.max_forecast && (
                <div className="bg-white rounded-lg p-3">
                  <p className="text-sm text-gray-600">Maximum Forecast</p>
                  <p className="text-xl font-bold text-gray-800">
                    {answer.forecast_summary.max_forecast.toLocaleString()}
                  </p>
                </div>
              )}
              {answer.forecast_summary.avg_forecast && (
                <div className="bg-white rounded-lg p-3">
                  <p className="text-sm text-gray-600">Average Forecast</p>
                  <p className="text-xl font-bold text-gray-800">
                    {Math.round(answer.forecast_summary.avg_forecast).toLocaleString()}
                  </p>
                </div>
              )}
              {answer.forecast_summary.total_periods && (
                <div className="bg-white rounded-lg p-3">
                  <p className="text-sm text-gray-600">Forecast Periods</p>
                  <p className="text-xl font-bold text-gray-800">
                    {answer.forecast_summary.total_periods}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <span className="text-sm text-gray-600">
              Confidence Level: <span className={`font-semibold ${
                answer.confidence === 'High' ? 'text-green-600' :
                answer.confidence === 'Medium' ? 'text-yellow-600' :
                'text-red-600'
              }`}>{answer.confidence}</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
