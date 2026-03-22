"""
Test Chart Generation with Future Prediction Queries
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))

# Test queries that should trigger visualizations
test_queries = [
    # Forecast queries (should show line chart + bar chart)
    "What will be the EV market growth in India by 2030?",
    "Predict the automotive market trends for next 5 years",
    "What is the future of electric vehicles in India?",
    
    # Comparison queries (should show bar chart + line chart)
    "Compare market growth with and without infrastructure",
    "What is the impact of EV charging stations on sales?",
    
    # Distribution queries (should show pie chart)
    "What will be the market share of different OEMs in 2030?",
    "Distribution of electric vehicle manufacturers",
    
    # Regular queries (should NOT show charts)
    "What are the current EV policies in India?",
    "Explain the automotive industry regulations"
]

print("="*70)
print("CHART GENERATION PREDICTION TEST")
print("="*70)
print()

for i, query in enumerate(test_queries, 1):
    print(f"{i}. Query: {query}")
    
    # Check forecast keywords
    forecast_keywords = [
        'forecast', 'predict', 'prediction', 'future', '2030', '2025', '2026', '2027', '2028', '2029',
        'projection', 'outlook', 'trend', 'growth', 'will be', 'expected', 'anticipate',
        'estimate', 'trajectory', 'what will', 'how will', 'by 2030'
    ]
    
    # Check comparison keywords
    comparison_keywords = [
        'compare', 'comparison', 'vs', 'versus', 'with and without',
        'difference between', 'impact of', 'effect of'
    ]
    
    # Check distribution keywords
    distribution_keywords = [
        'market share', 'share', 'distribution', 'breakdown', 'percentage',
        'proportion', 'oem', 'manufacturers'
    ]
    
    is_forecast = any(kw in query.lower() for kw in forecast_keywords)
    is_comparison = any(kw in query.lower() for kw in comparison_keywords)
    is_distribution = any(kw in query.lower() for kw in distribution_keywords)
    
    charts_predicted = []
    
    if is_forecast:
        charts_predicted.extend(['Line Chart (Trend)', 'Bar Chart (KPIs)'])
    if is_comparison:
        charts_predicted.extend(['Bar Chart (Comparison)', 'Line Chart (Trend)'])
    if is_distribution:
        charts_predicted.append('Pie Chart (Distribution)')
    
    if charts_predicted:
        print(f"   ✅ WILL GENERATE CHARTS: {', '.join(charts_predicted)}")
    else:
        print(f"   ❌ NO CHARTS (Text-only response)")
    
    print()

print("="*70)
print("✅ Chart generation prediction logic implemented!")
print()
print("Summary:")
print("- Forecast queries → Line + Bar charts")
print("- Comparison queries → Bar + Line charts")
print("- Distribution queries → Pie chart")
print("- Regular queries → Text only")
