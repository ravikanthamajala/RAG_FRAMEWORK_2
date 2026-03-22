"""
Advanced Analysis Routes - Research Novelty Features

API endpoints for:
1. Explainable AI - Transparent forecast explanations
2. Supply Chain Network Analysis - Dependency risk assessment
3. Enhanced Policy Impact Analysis

Research Innovation Endpoints for automotive market intelligence.
"""

from flask import Blueprint, request, jsonify
from app.agents.explainer import ForecastExplainer, explain_policy_recommendation
from app.agents.supply_chain_analyzer import SupplyChainNetworkAnalyzer

# Create advanced analysis blueprint
advanced_bp = Blueprint('advanced', __name__)

# Initialize analyzers
explainer = ForecastExplainer()
supply_chain_analyzer = SupplyChainNetworkAnalyzer()


@advanced_bp.route('/explain-forecast', methods=['POST', 'OPTIONS'])
def explain_forecast_endpoint():
    """
    Explain why a forecast was made using Explainable AI.
    
    Research Innovation: Transparent AI predictions with SHAP/LIME explanations
    
    Request Body:
        {
            "prediction": 25.5,  # Forecast value (e.g., EV adoption %)
            "features": {
                "subsidy_amount": 50000,
                "charging_infrastructure": 5000,
                "battery_cost": 150000,
                "consumer_awareness": 45
            }
        }
    
    Returns:
        JSON with:
        - top_drivers: Key factors influencing prediction
        - counterfactuals: What-if scenarios
        - sensitivity_analysis: How sensitive is the prediction
        - confidence_level: Confidence in prediction
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON content'}), 400
        
        prediction = data.get('prediction')
        features = data.get('features', {})
        
        if prediction is None or not features:
            return jsonify({'error': 'Missing prediction or features'}), 400
        
        # Generate explanation
        explanation = explainer.explain_forecast(
            prediction=float(prediction),
            input_features=features
        )
        
        return jsonify({
            'success': True,
            'explanation': explanation,
            'research_note': 'Explainable AI for transparent decision-making'
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Explanation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/analyze-supply-chain', methods=['POST', 'OPTIONS'])
def analyze_supply_chain_endpoint():
    """
    Analyze supply chain dependencies on Chinese suppliers.
    
    Research Innovation: Network topology analysis for strategic vulnerability assessment
    
    Request Body:
        {
            "oem_name": "Tata Motors",
            "supply_chain_data": [
                {
                    "supplier": "BYD Battery Co",
                    "supplier_country": "China",
                    "oem": "Tata Motors",
                    "component": "Lithium Battery",
                    "transaction_value": 500000000,
                    "criticality": 0.9
                }
            ]
        }
    
    Returns:
        JSON with:
        - dependency_score: 0-1 score of China dependency
        - risk_level: CRITICAL/HIGH/MEDIUM/LOW
        - critical_suppliers: List of bottleneck suppliers
        - alternatives: Alternative sourcing options
        - recommendations: Diversification strategy
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON content'}), 400
        
        oem_name = data.get('oem_name')
        supply_chain_data = data.get('supply_chain_data', [])
        
        if not oem_name:
            return jsonify({'error': 'Missing oem_name'}), 400
        
        # Build network from data
        if supply_chain_data:
            supply_chain_analyzer.build_network_from_data(supply_chain_data)
        else:
            # Use sample data for demonstration
            sample_data = _generate_sample_supply_chain_data(oem_name)
            supply_chain_analyzer.build_network_from_data(sample_data)
        
        # Analyze dependency
        analysis = supply_chain_analyzer.analyze_china_dependency(oem_name)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'research_note': 'Network centrality-based supply chain risk assessment'
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Supply chain analysis error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/simulate-disruption', methods=['POST', 'OPTIONS'])
def simulate_disruption_endpoint():
    """
    Simulate supply chain disruption scenario.
    
    Research Innovation: War-gaming supply shocks for preparedness
    
    Request Body:
        {
            "scenario": "china_trade_war",  # or "rare_earth_embargo", "battery_shortage"
            "supply_chain_data": [...]  # Optional
        }
    
    Returns:
        JSON with:
        - impact_percentage: Supply chain disruption %
        - affected_oems: List of impacted manufacturers
        - recovery_timeline: Estimated recovery time
        - mitigation_strategy: Recommended actions
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON content'}), 400
        
        scenario = data.get('scenario', 'china_trade_war')
        supply_chain_data = data.get('supply_chain_data', [])
        
        # Build network if data provided
        if supply_chain_data:
            supply_chain_analyzer.build_network_from_data(supply_chain_data)
        else:
            # Use sample data
            sample_data = _generate_sample_supply_chain_data("Indian Auto Industry")
            supply_chain_analyzer.build_network_from_data(sample_data)
        
        # Run simulation
        simulation_result = supply_chain_analyzer.simulate_disruption(scenario)
        
        return jsonify({
            'success': True,
            'simulation': simulation_result,
            'research_note': 'Monte Carlo-style disruption impact modeling'
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Disruption simulation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/explain-policy', methods=['POST', 'OPTIONS'])
def explain_policy_endpoint():
    """
    Explain why a policy is recommended with evidence.
    
    Research Innovation: Evidence-based policy justification
    
    Request Body:
        {
            "policy": "EV Purchase Subsidy",
            "impact_score": 0.85,
            "supporting_data": {
                "china_success_rate": 78,
                "cost_effectiveness": 120000,
                "market_readiness": 7.5
            }
        }
    
    Returns:
        JSON with:
        - recommendation: Strength of recommendation
        - evidence: Supporting data points
        - reasoning: Human-readable explanation
        - risks: Implementation risks
        - priority: Implementation timeline
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON content'}), 400
        
        policy = data.get('policy')
        impact_score = data.get('impact_score', 0.5)
        supporting_data = data.get('supporting_data', {})
        
        if not policy:
            return jsonify({'error': 'Missing policy name'}), 400
        
        # Generate explanation
        explanation = explain_policy_recommendation(
            policy=policy,
            impact_score=float(impact_score),
            supporting_data=supporting_data
        )
        
        return jsonify({
            'success': True,
            'explanation': explanation,
            'research_note': 'Transparent policy recommendation with evidence-based reasoning'
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Policy explanation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


def _generate_sample_supply_chain_data(oem_name: str) -> list:
    """
    Generate sample supply chain data for demonstration.
    
    In production, this should query actual supply chain database.
    """
    return [
        {
            "supplier": "BYD Battery Co",
            "supplier_country": "China",
            "oem": oem_name,
            "component": "Lithium Battery",
            "transaction_value": 500000000,
            "criticality": 0.95
        },
        {
            "supplier": "CATL",
            "supplier_country": "China",
            "oem": oem_name,
            "component": "Battery Management System",
            "transaction_value": 200000000,
            "criticality": 0.85
        },
        {
            "supplier": "Ningbo Motor Corp",
            "supplier_country": "China",
            "oem": oem_name,
            "component": "Electric Motor",
            "transaction_value": 300000000,
            "criticality": 0.90
        },
        {
            "supplier": "LG Chem",
            "supplier_country": "South Korea",
            "oem": oem_name,
            "component": "Lithium Battery",
            "transaction_value": 150000000,
            "criticality": 0.70
        },
        {
            "supplier": "Bosch India",
            "supplier_country": "India",
            "oem": oem_name,
            "component": "Power Electronics",
            "transaction_value": 100000000,
            "criticality": 0.60
        },
        {
            "supplier": "Sona BLW",
            "supplier_country": "India",
            "oem": oem_name,
            "component": "Electric Motor",
            "transaction_value": 80000000,
            "criticality": 0.50
        }
    ]
