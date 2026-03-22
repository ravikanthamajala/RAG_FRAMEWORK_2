"""
Query Route for Automotive Market Analysis

Handles user queries about China-India automotive market dynamics using the RAG agent.
Supports market analysis, policy impact assessment, and strategic recommendations for Indian OEMs.
"""

from flask import Blueprint, request, jsonify
from app.agents.rag_agent import query_agent, query_agent_with_charts

# Create query blueprint
query_bp = Blueprint('query', __name__)

@query_bp.route('/query', methods=['POST', 'OPTIONS'])
def query_documents():
    """
    Handle automotive market analysis queries.

    Accepts queries about:
    - China's automotive market trends and policies
    - India's automotive regulatory landscape
    - Policy impact analysis and market predictions
    - OEM competitiveness and strategy recommendations

    Returns:
        JSON response with market insights or error.
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    # Get JSON data from request
    data = request.get_json()
    
    # Handle empty or invalid JSON
    if not data:
        return jsonify({'error': 'Invalid JSON content'}), 400

    # Extract query from data
    query = data.get('query')

    # Check if query is provided
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # Query the agent
        response = query_agent(query)

        return jsonify({
            'response': response['response'],
            'sources': response['sources'],
            'confidence': response['confidence'],
            'confidence_reason': response.get('confidence_reason', ''),
            'confidence_score': response.get('confidence_score', 0),
            'query_type': response['query_type'],
            'num_sources': response['num_sources'],
            'intent': response['query_type'],
        }), 200
    except Exception as e:
        import traceback
        print(f"Query error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@query_bp.route('/query-with-charts', methods=['POST', 'OPTIONS'])
def query_documents_with_visualization():
    """
    Handle automotive market analysis queries with chart visualization.

    Accepts comparison queries and returns both text analysis and visual charts:
    - Comparison charts (bar, line, pie)
    - Market trend visualizations
    - Scenario analysis graphics

    Returns:
        JSON response with text insights and chart images (base64 encoded).
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204

    # Get JSON data from request
    data = request.get_json()
    
    # Handle empty or invalid JSON
    if not data:
        return jsonify({'error': 'Invalid JSON content'}), 400

    # Extract query from data
    query = data.get('query')

    # Check if query is provided
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # Query the agent with chart generation
        print(f"[query-charts] Query: {query}")
        response = query_agent_with_charts(query)

        intent = response.get('intent', response.get('query_type', 'GENERAL'))
        print(f"[query-charts] Intent: {intent} | Charts: {len(response.get('charts', []))} | Visualization: {response.get('has_visualization', False)}")

        return jsonify({
            'success': True,
            'response': response['text'],
            'sources': response['sources'],
            'confidence': response['confidence'],
            'confidence_reason': response.get('confidence_reason', ''),
            'confidence_score': response.get('confidence_score', 0),
            'intent': intent,
            'charts': response.get('charts', []),
            'has_visualization': response.get('has_visualization', False)
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Query with charts error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500