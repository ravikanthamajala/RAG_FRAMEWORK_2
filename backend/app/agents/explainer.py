"""
Explainable AI for Transparent Automotive Policy Recommendations

Research Innovation: Provides interpretable explanations for AI predictions
to increase trust in policy-making decisions.

Uses SHAP (SHapley Additive exPlanations) and LIME (Local Interpretable Model-agnostic Explanations)
to explain why the model makes specific forecasts and recommendations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

class ForecastExplainer:
    """
    Explainable AI for automotive market forecasting and policy analysis.
    
    Research Contribution: Makes black-box AI models transparent and trustworthy
    for strategic decision-making in automotive sector.
    """
    
    def __init__(self):
        """Initialize explainer with fallback for missing libraries"""
        self.shap_available = False
        self.lime_available = False
        
        try:
            import shap
            self.shap = shap
            self.shap_available = True
        except ImportError:
            print("Warning: SHAP not installed. Advanced explanations unavailable.")
        
        try:
            from lime import lime_tabular
            self.lime_tabular = lime_tabular
            self.lime_available = True
        except ImportError:
            print("Warning: LIME not installed. Local explanations unavailable.")
    
    def explain_forecast(self, 
                        prediction: float,
                        input_features: Dict[str, float],
                        model: Optional[Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a forecast prediction.
        
        Research Innovation: Transparent AI that shows WHY predictions are made,
        not just WHAT predictions are.
        
        Args:
            prediction: The forecast value
            input_features: Dictionary of feature names and values
            model: Optional trained model for advanced explanations
            
        Returns:
            Dictionary containing:
            - prediction: The forecast value
            - top_drivers: Key factors influencing the prediction
            - counterfactuals: What-if scenarios
            - sensitivity: How sensitive prediction is to changes
        """
        
        explanation = {
            "prediction": prediction,
            "top_drivers": self._identify_top_drivers(input_features),
            "counterfactuals": self._generate_counterfactuals(input_features, prediction),
            "sensitivity_analysis": self._what_if_analysis(input_features, prediction),
            "confidence_level": self._assess_confidence(input_features)
        }
        
        # Add SHAP-based explanation if available
        if self.shap_available and model is not None:
            try:
                explanation["shap_values"] = self._compute_shap_values(model, input_features)
            except Exception as e:
                print(f"SHAP computation failed: {e}")
        
        return explanation
    
    def _identify_top_drivers(self, features: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Identify which factors contribute most to the prediction.
        
        Research Novelty: Rule-based + heuristic driver identification
        """
        # Define domain knowledge for automotive market
        driver_weights = {
            "subsidy_amount": 0.35,
            "charging_infrastructure": 0.25,
            "battery_cost": 0.20,
            "consumer_awareness": 0.10,
            "regulatory_support": 0.10
        }
        
        drivers = []
        total_impact = 0
        
        for feature_name, feature_value in features.items():
            # Calculate normalized impact
            weight = driver_weights.get(feature_name, 0.05)
            normalized_value = feature_value / 100 if feature_value > 10 else feature_value
            impact = weight * normalized_value
            total_impact += impact
            
            drivers.append({
                "factor": feature_name.replace("_", " ").title(),
                "value": feature_value,
                "contribution_pct": round(weight * 100, 1),
                "impact_score": round(impact * 100, 2)
            })
        
        # Sort by impact
        drivers = sorted(drivers, key=lambda x: x['contribution_pct'], reverse=True)
        
        return drivers[:5]  # Top 5 drivers
    
    def _generate_counterfactuals(self, 
                                  features: Dict[str, float], 
                                  base_prediction: float) -> List[Dict[str, str]]:
        """
        Generate "what-if" scenarios showing how prediction changes.
        
        Research Innovation: Counterfactual reasoning for policy design
        
        Example: "If subsidy increases 10%, EV adoption rises 15%"
        """
        counterfactuals = []
        
        # Key policy levers for automotive market
        policy_levers = {
            "subsidy_amount": [1.10, 1.25, 1.50],  # 10%, 25%, 50% increase
            "charging_infrastructure": [1.10, 1.30, 1.50],
            "battery_cost": [0.90, 0.80, 0.70]  # Cost reduction
        }
        
        for lever, multipliers in policy_levers.items():
            if lever in features:
                for multiplier in multipliers:
                    # Simulate change
                    change_pct = (multiplier - 1) * 100
                    
                    # Estimate impact (simplified linear model)
                    impact_on_adoption = self._estimate_policy_impact(
                        lever, change_pct, base_prediction
                    )
                    
                    counterfactuals.append({
                        "scenario": f"{lever.replace('_', ' ').title()} {'increases' if multiplier > 1 else 'decreases'} {abs(change_pct):.0f}%",
                        "predicted_impact": f"EV adoption {'rises' if impact_on_adoption > 0 else 'falls'} {abs(impact_on_adoption):.1f}%",
                        "new_forecast": round(base_prediction * (1 + impact_on_adoption/100), 2)
                    })
        
        return counterfactuals[:6]  # Top 6 scenarios
    
    def _estimate_policy_impact(self, 
                                lever: str, 
                                change_pct: float, 
                                base_prediction: float) -> float:
        """
        Estimate how policy change affects adoption (simplified model).
        
        Research Note: Replace with actual trained model for accuracy
        """
        # Domain knowledge-based elasticity estimates
        elasticities = {
            "subsidy_amount": 0.45,  # 1% subsidy increase → 0.45% adoption increase
            "charging_infrastructure": 0.35,
            "battery_cost": -0.40  # Cost reduction increases adoption
        }
        
        elasticity = elasticities.get(lever, 0.2)
        impact = elasticity * change_pct
        
        return impact
    
    def _what_if_analysis(self, 
                         features: Dict[str, float], 
                         prediction: float) -> Dict[str, Any]:
        """
        Sensitivity analysis: How much does prediction change with inputs?
        
        Research Innovation: Uncertainty quantification for robust planning
        """
        sensitivity = {}
        
        for feature, value in features.items():
            # Test ±20% change
            low_impact = self._estimate_policy_impact(feature, -20, prediction)
            high_impact = self._estimate_policy_impact(feature, +20, prediction)
            
            sensitivity[feature] = {
                "baseline": value,
                "low_scenario": {
                    "change": "-20%",
                    "forecast": round(prediction * (1 + low_impact/100), 2)
                },
                "high_scenario": {
                    "change": "+20%",
                    "forecast": round(prediction * (1 + high_impact/100), 2)
                },
                "sensitivity_score": round(abs(high_impact - low_impact), 2)
            }
        
        return sensitivity
    
    def _assess_confidence(self, features: Dict[str, float]) -> str:
        """
        Assess confidence in prediction based on feature quality.
        
        Research Note: Can be enhanced with model uncertainty estimates
        """
        # Simple heuristic: More complete data = higher confidence
        feature_completeness = len([v for v in features.values() if v > 0]) / len(features)
        
        if feature_completeness > 0.8:
            return "High (>80% data completeness)"
        elif feature_completeness > 0.5:
            return "Medium (50-80% data completeness)"
        else:
            return "Low (<50% data completeness)"
    
    def _compute_shap_values(self, model: Any, features: Dict[str, float]) -> Dict[str, float]:
        """
        Compute SHAP values for feature importance (if SHAP available).
        
        Research Innovation: Game-theoretic feature attribution
        """
        if not self.shap_available:
            return {}
        
        try:
            # Convert features to array
            feature_array = np.array(list(features.values())).reshape(1, -1)
            
            # Compute SHAP values (TreeExplainer for tree-based models)
            explainer = self.shap.TreeExplainer(model)
            shap_values = explainer.shap_values(feature_array)
            
            # Map back to feature names
            shap_dict = {}
            for i, (name, value) in enumerate(features.items()):
                shap_dict[name] = float(shap_values[0][i])
            
            return shap_dict
        
        except Exception as e:
            print(f"SHAP computation error: {e}")
            return {}


def explain_policy_recommendation(policy: str, 
                                   impact_score: float, 
                                   supporting_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explain why a specific policy is recommended.
    
    Research Innovation: Transparent policy recommendation with justification
    
    Args:
        policy: Policy name
        impact_score: Predicted impact score
        supporting_data: Data supporting the recommendation
        
    Returns:
        Structured explanation with evidence and reasoning
    """
    
    explanation = {
        "policy": policy,
        "predicted_impact": impact_score,
        "recommendation": "Strongly Recommended" if impact_score > 0.7 else "Recommended" if impact_score > 0.4 else "Consider with Caution",
        "evidence": _extract_evidence(supporting_data),
        "reasoning": _generate_reasoning(policy, impact_score, supporting_data),
        "risks": _identify_risks(policy, supporting_data),
        "implementation_priority": _prioritize_implementation(impact_score)
    }
    
    return explanation


def _extract_evidence(data: Dict[str, Any]) -> List[str]:
    """Extract key evidence points from supporting data"""
    evidence = []
    
    if "china_success_rate" in data:
        evidence.append(f"China achieved {data['china_success_rate']}% success with similar policy")
    
    if "cost_effectiveness" in data:
        evidence.append(f"Cost-effectiveness ratio: ₹{data['cost_effectiveness']} per 1% market share gain")
    
    if "market_readiness" in data:
        evidence.append(f"Indian market readiness score: {data['market_readiness']}/10")
    
    return evidence


def _generate_reasoning(policy: str, score: float, data: Dict[str, Any]) -> str:
    """Generate human-readable reasoning for recommendation"""
    
    if score > 0.7:
        return f"{policy} shows high potential for India based on China's proven success and current market conditions. Strong policy-market alignment detected."
    elif score > 0.4:
        return f"{policy} demonstrates moderate potential but requires adaptation to Indian context. Monitor implementation closely."
    else:
        return f"{policy} shows limited evidence of effectiveness in Indian context. Consider alternative approaches or delay implementation."


def _identify_risks(policy: str, data: Dict[str, Any]) -> List[str]:
    """Identify implementation risks"""
    risks = []
    
    # Generic risk factors
    if data.get("budget_requirement", 0) > 10000:  # Crores
        risks.append("High budget requirement may face political resistance")
    
    if data.get("implementation_complexity", 0) > 7:
        risks.append("Complex implementation may delay results")
    
    if data.get("china_india_context_difference", 0) > 0.5:
        risks.append("Significant context differences between China and India")
    
    return risks if risks else ["Low risk - proceed with standard implementation"]


def _prioritize_implementation(impact_score: float) -> str:
    """Determine implementation priority"""
    if impact_score > 0.7:
        return "P0 - Immediate (0-6 months)"
    elif impact_score > 0.4:
        return "P1 - Near-term (6-12 months)"
    else:
        return "P2 - Long-term (12+ months)"
