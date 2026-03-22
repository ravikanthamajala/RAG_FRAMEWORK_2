'use client';

import React from 'react';

export default function PolicyInsights({ policyData, policyCharts }) {
  if (!policyData || policyData.error) {
    return null;
  }

  const {
    policies_adopted_from_china = [],
    policy_contribution_breakdown = {},
    policy_gaps = [],
    strategic_recommendations = [],
    forward_strategy = {}
  } = policyData;

  return (
    <div className="mt-8 space-y-6">
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg shadow-xl p-6">
        <h2 className="text-3xl font-bold mb-2">📋 Policy Analysis & Strategic Insights</h2>
        <p className="text-purple-100">
          Comprehensive analysis of policies adopted from China, their market impact, and strategic recommendations for India
        </p>
      </div>

      {/* Policy Adoption from China */}
      {policies_adopted_from_china && policies_adopted_from_china.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-3xl mr-3">🇨🇳 ➔ 🇮🇳</span>
            Policies Adopted from China
          </h3>
          <div className="space-y-4">
            {policies_adopted_from_china.map((policy, idx) => (
              <div key={idx} className="border-l-4 border-blue-500 pl-4 py-3 bg-blue-50 rounded-r-lg">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-lg text-gray-800">{policy.policy_name}</h4>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    policy.success_level === 'High' ? 'bg-green-500 text-white' :
                    policy.success_level === 'Medium' ? 'bg-yellow-500 text-white' :
                    'bg-gray-400 text-white'
                  }`}>
                    {policy.success_level} Success
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-semibold text-gray-600">China Implementation:</span>
                    <span className="ml-2 text-gray-800">{policy.china_year}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-600">India Adoption:</span>
                    <span className="ml-2 text-gray-800">{policy.india_year}</span>
                  </div>
                </div>
                <p className="mt-2 text-gray-700">
                  <span className="font-semibold">Adaptation:</span> {policy.adaptation}
                </p>
                <p className="mt-1 text-green-700 font-semibold">
                  <span className="text-gray-700">Forecast Impact:</span> {policy.forecast_impact}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Policy Charts */}
      {policyCharts && policyCharts.length > 0 && (
        <div className="space-y-6">
          {policyCharts.map((chart, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-2">{chart.title}</h3>
              <p className="text-gray-600 mb-4">{chart.description}</p>
              {chart.image && (
                <div className="overflow-x-auto">
                  <img 
                    src={chart.image} 
                    alt={chart.title}
                    className="max-w-full h-auto rounded-lg shadow-md"
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Policy Contribution Breakdown */}
      {policy_contribution_breakdown && Object.keys(policy_contribution_breakdown).length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-3xl mr-3">📊</span>
            Policy Contribution Breakdown
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(policy_contribution_breakdown).map(([category, data]) => (
              <div key={category} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-bold text-gray-800 capitalize">
                    {category.replace(/_/g, ' ')}
                  </h4>
                  <span className="text-2xl font-bold text-blue-600">
                    {data.percentage}%
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{data.description}</p>
                <p className="text-xs text-green-700 font-semibold">
                  📈 {data.impact}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Policy Gaps */}
      {policy_gaps && policy_gaps.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg shadow-lg p-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-3xl mr-3">⚠️</span>
            Policy Gaps to Address
          </h3>
          <ul className="space-y-2">
            {policy_gaps.map((gap, idx) => (
              <li key={idx} className="flex items-start space-x-3">
                <span className="text-yellow-600 font-bold mt-1">•</span>
                <span className="text-gray-700">{gap}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Strategic Recommendations */}
      {strategic_recommendations && strategic_recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-3xl mr-3">💡</span>
            Strategic Recommendations for India
          </h3>
          <div className="space-y-4">
            {strategic_recommendations.map((rec, idx) => (
              <div key={idx} className={`border-l-4 pl-4 py-3 rounded-r-lg ${
                rec.priority === 'Critical' || rec.priority === 'High' ? 'border-red-500 bg-red-50' :
                rec.priority === 'Medium' ? 'border-yellow-500 bg-yellow-50' :
                'border-green-500 bg-green-50'
              }`}>
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-lg text-gray-800">{rec.title}</h4>
                  <div className="flex gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      rec.priority === 'Critical' ? 'bg-red-600 text-white' :
                      rec.priority === 'High' ? 'bg-orange-500 text-white' :
                      rec.priority === 'Medium' ? 'bg-yellow-500 text-white' :
                      'bg-green-500 text-white'
                    }`}>
                      {rec.priority} Priority
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                  <div>
                    <span className="font-semibold text-gray-600">Timeline:</span>
                    <span className="ml-2 text-gray-800">{rec.timeline}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-600">Expected Impact:</span>
                    <span className="ml-2 text-green-700 font-semibold">{rec.impact}</span>
                  </div>
                </div>
                <p className="text-gray-700 mb-2">
                  <span className="font-semibold">Rationale:</span> {rec.rationale}
                </p>
                {rec.china_reference && (
                  <p className="text-xs text-blue-600 italic">
                    🔗 China Reference: {rec.china_reference}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Forward Strategy */}
      {forward_strategy && Object.keys(forward_strategy).length > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg shadow-lg p-6 border border-green-200">
          <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
            <span className="text-3xl mr-3">🚀</span>
            India Forward Strategy (2024-2030)
          </h3>
          <div className="space-y-6">
            {Object.entries(forward_strategy).map(([phase, actions]) => {
              const phaseColors = {
                'short_term_2024_2025': 'border-green-500 bg-green-50',
                'medium_term_2026_2028': 'border-blue-500 bg-blue-50',
                'long_term_2029_2030': 'border-purple-500 bg-purple-50'
              };
              const phaseLabels = {
                'short_term_2024_2025': 'Short Term (2024-2025)',
                'medium_term_2026_2028': 'Medium Term (2026-2028)',
                'long_term_2029_2030': 'Long Term (2029-2030)'
              };
              
              return (
                <div key={phase} className={`border-l-4 pl-4 py-3 rounded-r-lg ${phaseColors[phase] || 'border-gray-500 bg-gray-50'}`}>
                  <h4 className="font-bold text-lg text-gray-800 mb-3">
                    {phaseLabels[phase] || phase.replace(/_/g, ' ').toUpperCase()}
                  </h4>
                  <ul className="space-y-2">
                    {Array.isArray(actions) && actions.map((action, idx) => (
                      <li key={idx} className="flex items-start space-x-3">
                        <span className="text-gray-600 font-bold mt-1">{idx + 1}.</span>
                        <span className="text-gray-700">{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
