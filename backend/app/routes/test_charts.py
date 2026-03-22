"""
Simple test endpoint that returns mock charts immediately (no LLM needed)
"""
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

test_bp = Blueprint('test', __name__)

@test_bp.route('/test-charts', methods=['POST', 'OPTIONS'])
@cross_origin()
def test_charts():
    """Return mock data with charts for testing frontend display"""
    
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json()
    query = data.get('query', 'Test query')
    
    # Mock response
    response = {
        'success': True,
        'response': f"""Based on analysis of automotive market data, here are the key insights for: "{query}"

The EV market in India is projected to grow significantly by 2030:
- Market penetration will reach 30-35% by 2030 (Source 1)
- Infrastructure development will accelerate adoption by 12-15% (Source 2)
- Government policies will drive 40% of the growth (Source 3)

Key metrics show strong growth trajectory across all indicators.""",
        
        'sources': [
            {
                'source_id': 1,
                'filename': 'India_EV_Market_2024.csv',
                'similarity_score': 0.92,
                'document_type': 'Excel'
            },
            {
                'source_id': 2,
                'filename': 'automotive_forecast_2030.pdf',
                'similarity_score': 0.87,
                'document_type': 'PDF/Text'
            },
            {
                'source_id': 3,
                'filename': 'policy_analysis.xlsx',
                'similarity_score': 0.85,
                'document_type': 'Excel'
            }
        ],
        
        'confidence': 'High',
        'query_type': 'FORECAST',
        
        'charts': [
            {
                'type': 'line',
                'title': 'EV Market Growth Forecast 2024-2030',
                'description': 'Projected EV adoption rate showing steady growth',
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='  # Minimal valid PNG
            },
            {
                'type': 'bar',
                'title': 'Key Performance Indicators',
                'description': 'Comparison of market metrics',
                'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='  # Minimal valid PNG
            }
        ],
        
        'has_visualization': True
    }
    
    return jsonify(response), 200
