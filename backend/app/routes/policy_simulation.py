"""
Policy Simulation Routes - Interactive policy adjustment and forecasting
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app.agents.policy_simulator import PolicySimulator

policy_sim_bp = Blueprint('policy_simulation', __name__)
simulator = PolicySimulator()


@policy_sim_bp.route('/run-simulation', methods=['POST', 'OPTIONS'])
@cross_origin()
def run_simulation_standalone():
    """
    Standalone simulation endpoint. Does NOT require pre-uploaded forecast data.
    Accepts 6 policy slider values (0-100 each) and returns year-by-year
    projections with and without the policy mix applied.

    Request Body:
        {
            "charging_infra":    <0-100>,
            "subsidies":         <0-100>,
            "manufacturing":     <0-100>,
            "rnd":               <0-100>,
            "mandates":          <0-100>,
            "state_incentives":  <0-100>
        }

    Response:
        {
            "status": "success",
            "years": [2024, 2025, ..., 2030],
            "without_policy": [...],
            "with_policy": [...],
            "policy_score": <0-100>,
            "base_growth_rate": <float>,
            "policy_growth_boost": <float>,
            "effective_growth_rate": <float>,
            "insights": [...]
        }
    """
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json() or {}

        # Weighted impact: charging_infra 30%, subsidies 25%, manufacturing 20%,
        # rnd 10%, mandates 10%, state_incentives 5%
        charging_infra   = max(0.0, min(100.0, float(data.get('charging_infra',   50))))
        subsidies        = max(0.0, min(100.0, float(data.get('subsidies',        50))))
        manufacturing    = max(0.0, min(100.0, float(data.get('manufacturing',    50))))
        rnd              = max(0.0, min(100.0, float(data.get('rnd',              50))))
        mandates         = max(0.0, min(100.0, float(data.get('mandates',         50))))
        state_incentives = max(0.0, min(100.0, float(data.get('state_incentives', 50))))
        new_ports        = bool(data.get('new_ports', False))
        new_highways     = bool(data.get('new_highways', False))
        current_value    = max(1.0, float(data.get('current_value', 4_200_000)))

        # Composite policy score  (0-100)
        policy_score = (
            charging_infra   * 0.30 +
            subsidies        * 0.25 +
            manufacturing    * 0.20 +
            rnd              * 0.10 +
            mandates         * 0.10 +
            state_incentives * 0.05
        )

        # Growth rates using compound annual growth.
        base_growth_rate = 0.05
        policy_mix_boost = (policy_score / 100.0) * 0.025
        port_construction_boost    = 0.03  if new_ports    else 0.0
        highway_construction_boost = 0.025 if new_highways else 0.0
        effective_growth_rate = base_growth_rate + policy_mix_boost + port_construction_boost + highway_construction_boost

        years = list(range(2025, 2051))
        without_policy = [
            round(current_value * ((1 + base_growth_rate) ** i))
            for i in range(len(years))
        ]
        with_policy = [
            round(current_value * ((1 + effective_growth_rate) ** i))
            for i in range(len(years))
        ]

        print(
            f"[run-simulation] Base Growth: {base_growth_rate:.4f}, "
            f"Policy Impact: {policy_mix_boost:.4f}, "
            f"Port Impact: {port_construction_boost:.4f}, "
            f"Highway Impact: {highway_construction_boost:.4f}, "
            f"Final Growth: {effective_growth_rate:.4f}, "
            f"Policy Score: {policy_score:.2f}, New Ports: {new_ports}, New Highways: {new_highways}"
        )

        # Simple insights
        insights = []
        if policy_score >= 70:
            insights.append(f"🚀 Strong policy mix (score {policy_score:.0f}/100) — {(policy_mix_boost * 100):.1f}% additional annual growth")
        elif policy_score >= 40:
            insights.append(f"📊 Moderate policy mix (score {policy_score:.0f}/100) — {(policy_mix_boost * 100):.1f}% additional annual growth")
        else:
            insights.append(f"⚠️ Weak policy mix (score {policy_score:.0f}/100) — only {(policy_mix_boost * 100):.1f}% additional annual growth")

        if new_ports:
            insights.append("🚢 New port construction is enabled — adding a dedicated 3.0% logistics uplift to EV adoption growth")
        if new_highways:
            insights.append("🛣️ New highway construction is enabled — adding a dedicated 2.5% connectivity uplift to EV adoption growth")
        if not new_ports and not new_highways:
            insights.append("🏗️ No new infrastructure construction — forecast follows baseline growth plus any broader policy mix only")

        if charging_infra < 30:
            insights.append("⚡ Charging infrastructure is low — a major adoption barrier; consider raising it above 50")
        if subsidies < 30:
            insights.append("💰 Consumer subsidies are low — demand stimulation is key for early-market EV uptake")
        if manufacturing >= 70:
            insights.append("🏭 Strong manufacturing support aligns with PLI scheme objectives")

        by_2050_without = without_policy[-1]
        by_2050_with    = with_policy[-1]
        delta           = by_2050_with - by_2050_without
        insights.append(
            f"📈 By 2050 this scenario adds ~{delta:,} units "
            f"({((delta / by_2050_without) * 100):.1f}% over baseline)"
        )

        return jsonify({
            'status': 'success',
            'years': years,
            'without_policy': without_policy,
            'with_policy': with_policy,
            'policy_score': round(policy_score, 1),
            'base_growth_rate': round(base_growth_rate * 100, 2),
            'policy_growth_boost': round(policy_mix_boost * 100, 2),
            'port_construction_boost': round(port_construction_boost * 100, 2),
            'highway_construction_boost': round(highway_construction_boost * 100, 2),
            'effective_growth_rate': round(effective_growth_rate * 100, 2),
            'debug': {
                'base_growth': round(base_growth_rate, 4),
                'policy_impact': round(policy_mix_boost, 4),
                'port_impact': round(port_construction_boost, 4),
                'highway_impact': round(highway_construction_boost, 4),
                'final_growth': round(effective_growth_rate, 4),
                'new_ports': new_ports,
                'new_highways': new_highways,
            },
            'insights': insights,
        }), 200

    except Exception as e:
        import traceback
        print(f"[run-simulation] error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@policy_sim_bp.route('/policy-simulation/simulate', methods=['POST', 'OPTIONS'])
@cross_origin()
def simulate_policy_changes():
    """
    Simulate forecast changes based on policy adjustments.
    
    Request Body:
        {
            "base_forecast": [...],  // Original forecast data
            "policy_adjustments": {
                "manufacturing_incentives": 20,
                "consumer_subsidies": 15,
                ...
            }
        }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        base_forecast = data.get('base_forecast', [])
        policy_adjustments = data.get('policy_adjustments', {})
        
        if not base_forecast:
            return jsonify({'error': 'base_forecast required'}), 400
        
        # Use default policies if none provided
        if not policy_adjustments:
            policy_adjustments = {
                k: v['base_contribution'] 
                for k, v in simulator.policies.items()
            }
        
        # Run simulation
        result = simulator.simulate_forecast(base_forecast, policy_adjustments)
        
        return jsonify({
            'status': 'success',
            'simulation': result
        }), 200
    
    except Exception as e:
        import traceback
        print(f"Simulation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@policy_sim_bp.route('/policy-simulation/policies', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_policy_definitions():
    """Get all available policies with their constraints."""
    if request.method == 'OPTIONS':
        return '', 204
    
    return jsonify({
        'status': 'success',
        'policies': simulator.policies
    }), 200


@policy_sim_bp.route('/policy-simulation/presets', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_policy_presets():
    """Get predefined policy scenarios."""
    if request.method == 'OPTIONS':
        return '', 204
    
    return jsonify({
        'status': 'success',
        'presets': simulator.get_policy_presets()
    }), 200
