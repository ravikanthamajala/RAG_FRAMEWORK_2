"""
Forecast API routes for India automotive market 2030 scenario analysis
"""
from flask import Blueprint, request, jsonify, send_file
from app.agents.india_forecast_2030 import India2030Forecaster
import os

forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/forecast/india-2030', methods=['GET', 'POST', 'OPTIONS'])
def india_2030_forecast():
    """
    Generate India automotive market forecast for 2030
    Comparison: With vs Without China Policies
    Includes visualizations
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Generate forecasts
        forecaster = India2030Forecaster()
        
        # Generate all visualizations
        chart_result = forecaster.generate_visualizations()
        
        # Generate detailed report
        report = forecaster.generate_report()
        
        return jsonify({
            "status": "success",
            "message": "India 2030 forecast generated successfully with 6 visualization charts",
            "report": report,
            "charts": {
                "status": chart_result["status"],
                "charts_generated": chart_result["charts_generated"],
                "chart_urls": [
                    "/static/charts/01_ev_percentage_comparison.png",
                    "/static/charts/02_ev_units_comparison.png",
                    "/static/charts/03_total_sales_comparison.png",
                    "/static/charts/04_growth_rate_comparison.png",
                    "/static/charts/05_economic_impact.png",
                    "/static/charts/06_market_composition.png"
                ]
            }
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@forecast_bp.route('/chart/<filename>', methods=['GET'])
def get_chart(filename):
    """Serve individual chart image"""
    try:
        chart_path = os.path.join('app', 'static', 'charts', filename)
        if os.path.exists(chart_path):
            return send_file(chart_path, mimetype='image/png')
        return jsonify({'error': 'Chart not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
