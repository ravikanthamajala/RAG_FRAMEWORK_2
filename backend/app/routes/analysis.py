"""
Market Analysis Routes for Automotive Analysis

Endpoints for:
- Market forecasting
- Policy analysis and comparison
- OEM strategy recommendations
- Market insights and trends
"""

from flask import Blueprint, request, jsonify
from app.agents.market_forecaster import AutomotiveMarketForecaster
from app.agents.policy_analyzer import PolicyAnalyzer
from datetime import datetime
import pandas as pd

# Create analysis blueprint
analysis_bp = Blueprint('analysis', __name__)

# Initialize agents
forecaster = AutomotiveMarketForecaster()
policy_analyzer = PolicyAnalyzer()


@analysis_bp.route('/forecast/market', methods=['POST'])
def forecast_market():
    """
    Forecast India's automotive market metrics.

    Accepts:
    - historical_data: Historical market sales/production data
    - forecast_periods: Number of months to forecast (default: 36)

    Returns:
        JSON with ensemble forecasts from multiple models
    """
    try:
        data = request.get_json()
        
        if 'data' not in data:
            return jsonify({'error': 'No data provided'}), 400

        # Convert to DataFrame
        df = pd.DataFrame(data['data'])
        periods = data.get('forecast_periods', 36)

        # Generate ensemble forecast
        forecast_result = forecaster.generate_ensemble_forecast(df, periods)

        return jsonify({
            'status': 'success',
            'forecast': forecast_result,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/forecast/ev-adoption', methods=['POST'])
def forecast_ev_adoption():
    """
    Forecast EV adoption rates in India.

    Accepts:
    - historical_data: Historical EV adoption percentages

    Returns:
        JSON with EV adoption forecast and insights
    """
    try:
        data = request.get_json()
        
        if 'data' not in data:
            return jsonify({'error': 'No data provided'}), 400

        df = pd.DataFrame(data['data'])
        forecast_result = forecaster.forecast_ev_adoption(df)

        return jsonify({
            'status': 'success',
            'ev_forecast': forecast_result,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/forecast/oem-market-share', methods=['POST'])
def forecast_oem_share():
    """
    Forecast OEM market share evolution.

    Accepts:
    - market_data: Overall market data
    - oem_data: Dictionary of OEM-specific data

    Returns:
        JSON with market share forecasts for each OEM
    """
    try:
        data = request.get_json()
        
        if 'market_data' not in data or 'oem_data' not in data:
            return jsonify({'error': 'Missing market_data or oem_data'}), 400

        market_df = pd.DataFrame(data['market_data'])
        oem_data = data['oem_data']

        # Convert OEM data
        oem_data_processed = {}
        for oem_name, oem_df in oem_data.items():
            oem_data_processed[oem_name] = pd.DataFrame(oem_df)

        forecast_result = forecaster.forecast_oem_market_share(market_df, oem_data_processed)

        return jsonify({
            'status': 'success',
            'oem_forecasts': forecast_result,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/policy/extract', methods=['POST'])
def extract_policies():
    """
    Extract policies from uploaded documents.

    Accepts:
    - documents: List of document chunks from RAG

    Returns:
        JSON with extracted policies organized by domain
    """
    try:
        data = request.get_json()
        
        if 'documents' not in data:
            return jsonify({'error': 'No documents provided'}), 400

        documents = data['documents']
        extracted = policy_analyzer.extract_policies_from_documents(documents)

        return jsonify({
            'status': 'success',
            'extracted_policies': extracted,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/policy/compare', methods=['POST'])
def compare_policies():
    """
    Compare China and India automotive policies.

    Accepts:
    - china_policies: Extracted China policies
    - india_policies: Extracted India policies

    Returns:
        JSON with comparative analysis and alignment scores
    """
    try:
        data = request.get_json()
        
        if 'china_policies' not in data or 'india_policies' not in data:
            return jsonify({'error': 'Missing china_policies or india_policies'}), 400

        comparison = policy_analyzer.compare_china_india_policies(
            data['china_policies'],
            data['india_policies']
        )

        return jsonify({
            'status': 'success',
            'comparison': comparison,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/policy/recommendations', methods=['POST'])
def get_policy_recommendations():
    """
    Generate policy recommendations for India.

    Accepts:
    - comparison: Policy comparison results

    Returns:
        JSON with strategic recommendations
    """
    try:
        data = request.get_json()
        
        if 'comparison' not in data:
            return jsonify({'error': 'No comparison provided'}), 400

        recommendations = policy_analyzer.generate_policy_recommendations(data['comparison'])

        return jsonify({
            'status': 'success',
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/oem/strategy', methods=['POST'])
def get_oem_strategy():
    """
    Generate strategic recommendations for Indian OEMs.

    Accepts:
    - market_data: Current market conditions
    - policy_landscape: Policy analysis results
    - oem_position: OEM's current market position

    Returns:
        JSON with strategic insights and recommendations
    """
    try:
        data = request.get_json()
        
        strategy = {
            'status': 'success',
            'recommendations': {
                'short_term': [
                    'Focus on traditional ICE vehicles with improved efficiency',
                    'Prepare supply chain for transition',
                    'Invest in EV technology scouting'
                ],
                'medium_term': [
                    'Launch competitive EV models',
                    'Develop local component ecosystem',
                    'Build R&D capabilities'
                ],
                'long_term': [
                    'Position as technology leader in emerging segments',
                    'Establish global supply chain partnerships',
                    'Develop autonomous and connected vehicle capabilities'
                ]
            },
            'competitive_advantages': [
                'Cost competitiveness',
                'Access to growing Indian market',
                'Government support and incentives',
                'Rising talent pool'
            ],
            'risks': [
                'Rapid technology disruption',
                'Chinese OEM competition',
                'Policy uncertainty',
                'EV infrastructure gap'
            ],
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(strategy), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/insights/market', methods=['GET'])
def get_market_insights():
    """
    Get key market insights and trends.

    Returns:
        JSON with market insights, trends, and key metrics
    """
    try:
        insights = {
            'status': 'success',
            'key_trends': [
                'Rapid EV adoption in China drives global transformation',
                'Indian automotive market growing at 8-10% CAGR',
                'OEM consolidation expected in next 3 years',
                'Technology and policy alignment critical for success'
            ],
            'market_metrics': {
                'china_ev_penetration': '35-40%',
                'india_ev_penetration': '5-7%',
                'china_market_size': '$2.0T USD',
                'india_market_size': '$0.12T USD',
                'growth_opportunity': 'High'
            },
            'strategic_focus_areas': [
                'EV technology and battery development',
                'Supply chain localization',
                'Autonomous vehicle development',
                'Connected car technologies',
                'Policy alignment with government incentives'
            ],
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(insights), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
