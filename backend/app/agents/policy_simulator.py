"""
Policy Simulator Agent - Simulates forecast changes based on policy adjustments
Allows users to experiment with different policy contribution scenarios
"""

import numpy as np
from typing import Dict, List, Any
import pandas as pd


class PolicySimulator:
    """Simulates forecast impact based on policy contribution adjustments."""
    
    # Default policy contributions (based on China's experience)
    DEFAULT_POLICIES = {
        'manufacturing_incentives': {
            'name': 'Manufacturing Incentives (PLI Scheme)',
            'base_contribution': 18,  # % contribution to growth
            'min': 0,
            'max': 30,
            'description': 'Subsidies for local EV manufacturing'
        },
        'consumer_subsidies': {
            'name': 'Consumer Subsidies (FAME II)',
            'base_contribution': 15,
            'min': 0,
            'max': 25,
            'description': 'Direct purchase incentives for buyers'
        },
        'charging_infrastructure': {
            'name': 'Charging Infrastructure Investment',
            'base_contribution': 12,
            'min': 0,
            'max': 20,
            'description': 'Public charging network expansion'
        },
        'regulatory_mandates': {
            'name': 'Regulatory Mandates (EV Quotas)',
            'base_contribution': 10,
            'min': 0,
            'max': 20,
            'description': 'Mandatory EV sales targets for OEMs'
        },
        'rd_investment': {
            'name': 'R&D and Battery Tech Investment',
            'base_contribution': 8,
            'min': 0,
            'max': 15,
            'description': 'Battery technology and innovation funding'
        },
        'import_duties': {
            'name': 'Import Duty Adjustments',
            'base_contribution': 5,
            'min': -10,  # Can reduce forecast if too high
            'max': 10,
            'description': 'Customs duty on EV imports'
        },
        'state_policies': {
            'name': 'State-Level Incentives',
            'base_contribution': 7,
            'min': 0,
            'max': 15,
            'description': 'Regional tax benefits and subsidies'
        }
    }
    
    def __init__(self):
        self.policies = self.DEFAULT_POLICIES.copy()
    
    def simulate_forecast(
        self, 
        base_forecast_data: List[Dict],
        policy_adjustments: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Simulate new forecast based on policy contribution adjustments.
        
        Args:
            base_forecast_data: Original forecast data points
            policy_adjustments: Dict of {policy_key: contribution_percentage}
            
        Returns:
            Simulated forecast with new projections and insights
        """
        # Calculate total policy impact change
        base_total = sum(p['base_contribution'] for p in self.policies.values())
        adjusted_total = sum(policy_adjustments.values())
        
        # Calculate growth multiplier
        multiplier = adjusted_total / base_total if base_total > 0 else 1.0
        
        # Apply multiplier to forecast
        simulated_data = []
        for point in base_forecast_data:
            period = point.get('period', point.get('date', ''))
            original_forecast = point.get('forecast', point.get('value', 0))
            
            # Apply growth multiplier (more impact in later periods)
            period_index = base_forecast_data.index(point)
            total_periods = len(base_forecast_data)
            time_factor = (period_index / total_periods) ** 0.5  # Square root for smoother curve
            
            adjusted_forecast = original_forecast * (1 + (multiplier - 1) * time_factor)
            
            simulated_data.append({
                'period': period,
                'original_forecast': original_forecast,
                'adjusted_forecast': adjusted_forecast,
                'difference': adjusted_forecast - original_forecast,
                'percentage_change': ((adjusted_forecast / original_forecast) - 1) * 100 if original_forecast > 0 else 0
            })
        
        # Generate insights
        insights = self._generate_insights(
            policy_adjustments, 
            simulated_data, 
            multiplier
        )
        
        return {
            'simulated_data': simulated_data,
            'policy_contributions': policy_adjustments,
            'total_contribution': adjusted_total,
            'growth_multiplier': multiplier,
            'insights': insights,
            'comparison': {
                'original_end_value': base_forecast_data[-1].get('forecast', 0) if base_forecast_data else 0,
                'simulated_end_value': simulated_data[-1]['adjusted_forecast'] if simulated_data else 0,
                'total_change': simulated_data[-1]['difference'] if simulated_data else 0,
                'percentage_improvement': ((multiplier - 1) * 100)
            }
        }
    
    def _generate_insights(
        self, 
        policy_adjustments: Dict[str, float],
        simulated_data: List[Dict],
        multiplier: float
    ) -> List[str]:
        """Generate strategic insights based on policy adjustments."""
        insights = []
        
        # Overall impact
        if multiplier > 1.1:
            insights.append(f"🚀 Strong policy mix: {((multiplier - 1) * 100):.1f}% forecasted growth improvement")
        elif multiplier < 0.9:
            insights.append(f"⚠️ Weak policy mix: {((1 - multiplier) * 100):.1f}% forecasted growth reduction")
        else:
            insights.append(f"📊 Moderate policy mix: {((multiplier - 1) * 100):.1f}% forecasted growth change")
        
        # Top contributors
        sorted_policies = sorted(
            policy_adjustments.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        insights.append(
            f"🏆 Top contributors: " + 
            ", ".join([f"{self.policies[k]['name']} ({v}%)" for k, v in sorted_policies])
        )
        
        # Recommendations
        for policy_key, contribution in policy_adjustments.items():
            policy_info = self.policies[policy_key]
            base = policy_info['base_contribution']
            
            if contribution > base * 1.5:
                insights.append(
                    f"💡 {policy_info['name']}: Strong focus ({contribution}%). "
                    f"Consider infrastructure support for implementation."
                )
            elif contribution < base * 0.5 and base > 5:
                insights.append(
                    f"⚠️ {policy_info['name']}: Low allocation ({contribution}%). "
                    f"This may limit growth potential."
                )
        
        # China comparison
        china_successful_mix = {
            'manufacturing_incentives': 20,
            'consumer_subsidies': 18,
            'charging_infrastructure': 15
        }
        
        similarity_score = self._calculate_similarity(policy_adjustments, china_successful_mix)
        if similarity_score > 0.7:
            insights.append(
                f"🇨🇳 {similarity_score * 100:.0f}% similar to China's successful policy mix"
            )
        
        return insights
    
    def _calculate_similarity(self, mix1: Dict, mix2: Dict) -> float:
        """Calculate cosine similarity between two policy mixes."""
        keys = set(mix1.keys()) & set(mix2.keys())
        if not keys:
            return 0.0
        
        vec1 = np.array([mix1.get(k, 0) for k in keys])
        vec2 = np.array([mix2.get(k, 0) for k in keys])
        
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        
        return dot_product / norm_product if norm_product > 0 else 0.0
    
    def get_policy_presets(self) -> Dict[str, Dict]:
        """Get predefined policy scenarios."""
        return {
            'china_model': {
                'name': 'China Success Model',
                'description': 'Based on China\'s successful EV transition (2015-2020)',
                'policies': {
                    'manufacturing_incentives': 20,
                    'consumer_subsidies': 18,
                    'charging_infrastructure': 15,
                    'regulatory_mandates': 12,
                    'rd_investment': 10,
                    'import_duties': 3,
                    'state_policies': 8
                }
            },
            'aggressive_growth': {
                'name': 'Aggressive Growth Strategy',
                'description': 'Maximum incentives for rapid market penetration',
                'policies': {
                    'manufacturing_incentives': 25,
                    'consumer_subsidies': 22,
                    'charging_infrastructure': 18,
                    'regulatory_mandates': 15,
                    'rd_investment': 12,
                    'import_duties': 5,
                    'state_policies': 12
                }
            },
            'balanced_approach': {
                'name': 'Balanced Approach',
                'description': 'Moderate incentives across all policy areas',
                'policies': {
                    'manufacturing_incentives': 15,
                    'consumer_subsidies': 15,
                    'charging_infrastructure': 12,
                    'regulatory_mandates': 10,
                    'rd_investment': 10,
                    'import_duties': 5,
                    'state_policies': 10
                }
            },
            'infrastructure_focus': {
                'name': 'Infrastructure-Led Growth',
                'description': 'Prioritize charging infrastructure development',
                'policies': {
                    'manufacturing_incentives': 12,
                    'consumer_subsidies': 10,
                    'charging_infrastructure': 25,
                    'regulatory_mandates': 8,
                    'rd_investment': 8,
                    'import_duties': 4,
                    'state_policies': 6
                }
            },
            'current_india': {
                'name': 'Current India Policy Mix',
                'description': 'Existing policy framework (2024)',
                'policies': {
                    'manufacturing_incentives': 18,
                    'consumer_subsidies': 15,
                    'charging_infrastructure': 12,
                    'regulatory_mandates': 10,
                    'rd_investment': 8,
                    'import_duties': 5,
                    'state_policies': 7
                }
            }
        }
