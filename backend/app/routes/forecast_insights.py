"""
Forecast Insights Routes - Answer questions about forecast results
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app.agents.forecast_insights_agent import ForecastInsightsAgent

forecast_insights_bp = Blueprint('forecast_insights', __name__)
insights_agent = ForecastInsightsAgent()

# Store recent forecasts in memory (in production, use database)
recent_forecasts = {}

@forecast_insights_bp.route('/forecast-insights/ask', methods=['POST', 'OPTIONS'])
@cross_origin()
def ask_about_forecast():
    """
    Answer questions about forecast results.
    
    Request Body:
        {
            "forecast_id": "abc123",  // ID of the forecast to query
            "question": "What will be the growth rate in 2025?"
        }
        
    OR provide forecast data directly:
        {
            "forecast_data": { ... },  // Full forecast result
            "question": "What is the trend?"
        }
    
    Returns:
        JSON with answer, insights, and summary
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Get forecast data
        forecast_data = None
        
        if 'forecast_data' in data:
            forecast_data = data['forecast_data']
        elif 'forecast_id' in data:
            forecast_id = data['forecast_id']
            forecast_data = recent_forecasts.get(forecast_id)
            
            if not forecast_data:
                return jsonify({'error': 'Forecast not found. Please provide forecast_data directly.'}), 404
        else:
            return jsonify({'error': 'Provide either forecast_id or forecast_data'}), 400
        
        # Analyze and answer
        result = insights_agent.analyze_forecast_results(forecast_data, question)
        
        return jsonify({
            'status': 'success',
            'result': result
        }), 200
    
    except Exception as e:
        import traceback
        print(f"Forecast insights error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@forecast_insights_bp.route('/forecast-insights/store', methods=['POST', 'OPTIONS'])
@cross_origin()
def store_forecast():
    """
    Store forecast results for later querying.
    
    Request Body:
        {
            "forecast_id": "abc123",
            "forecast_data": { ... }
        }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        forecast_id = data.get('forecast_id')
        forecast_data = data.get('forecast_data')
        
        if not forecast_id or not forecast_data:
            return jsonify({'error': 'forecast_id and forecast_data required'}), 400
        
        recent_forecasts[forecast_id] = forecast_data
        
        return jsonify({
            'status': 'success',
            'message': f'Forecast {forecast_id} stored successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
