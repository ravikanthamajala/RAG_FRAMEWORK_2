"""
Supply Chain Network Analysis for Automotive Sector

Research Innovation: Quantifies supply chain vulnerabilities using network topology analysis.
Identifies dependencies on Chinese suppliers and recommends diversification strategies.

Uses graph theory to model supply chains and measure strategic risks.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: NetworkX not installed. Supply chain analysis will use fallback methods.")


class SupplyChainNetworkAnalyzer:
    """
    Network-based analysis of automotive supply chain vulnerabilities.
    
    Research Contribution: Quantifies strategic dependency on Chinese suppliers
    using centrality metrics and disruption simulation.
    """
    
    def __init__(self):
        """Initialize supply chain network"""
        if NETWORKX_AVAILABLE:
            self.network = nx.DiGraph()
        else:
            self.network = None
        self.china_suppliers = []
        self.indian_oems = []
    
    def build_network_from_data(self, supply_chain_data: List[Dict[str, Any]]) -> None:
        """
        Build supply chain network graph from data.
        
        Args:
            supply_chain_data: List of supplier-OEM relationships
                [{
                    "supplier": "BYD Battery",
                    "supplier_country": "China",
                    "oem": "Tata Motors",
                    "component": "Lithium Battery",
                    "transaction_value": 500000000,  # Annual value in rupees
                    "criticality": 0.9  # 0-1 scale
                }]
        """
        if not NETWORKX_AVAILABLE:
            print("NetworkX not available. Using simplified analysis.")
            self._build_simplified_network(supply_chain_data)
            return
        
        for relationship in supply_chain_data:
            supplier = relationship['supplier']
            oem = relationship['oem']
            
            # Add nodes
            self.network.add_node(
                supplier,
                node_type='supplier',
                country=relationship.get('supplier_country', 'Unknown')
            )
            self.network.add_node(
                oem,
                node_type='oem',
                country='India'
            )
            
            # Add edge with attributes
            self.network.add_edge(
                supplier,
                oem,
                component=relationship['component'],
                value=relationship.get('transaction_value', 0),
                criticality=relationship.get('criticality', 0.5)
            )
            
            # Track Chinese suppliers and Indian OEMs
            if relationship.get('supplier_country') == 'China':
                if supplier not in self.china_suppliers:
                    self.china_suppliers.append(supplier)
            
            if oem not in self.indian_oems:
                self.indian_oems.append(oem)
    
    def analyze_china_dependency(self, indian_oem: str) -> Dict[str, Any]:
        """
        Quantify OEM's dependency on Chinese suppliers.
        
        Research Innovation: Network centrality-based risk quantification
        
        Args:
            indian_oem: Name of Indian OEM to analyze
            
        Returns:
            Dictionary with dependency metrics and risk assessment
        """
        if not NETWORKX_AVAILABLE:
            return self._simplified_dependency_analysis(indian_oem)
        
        # Calculate various centrality metrics
        dependency_metrics = {
            "oem": indian_oem,
            "china_dependency_score": self._calculate_dependency_score(indian_oem),
            "critical_chinese_suppliers": self._find_critical_suppliers(indian_oem),
            "alternative_suppliers": self._find_alternatives(indian_oem),
            "risk_level": "",
            "diversification_recommendations": []
        }
        
        # Assess risk level
        score = dependency_metrics["china_dependency_score"]
        if score > 0.7:
            dependency_metrics["risk_level"] = "CRITICAL"
            dependency_metrics["priority"] = "P0 - Immediate action required"
        elif score > 0.4:
            dependency_metrics["risk_level"] = "HIGH"
            dependency_metrics["priority"] = "P1 - Address within 6 months"
        elif score > 0.2:
            dependency_metrics["risk_level"] = "MEDIUM"
            dependency_metrics["priority"] = "P2 - Plan for diversification"
        else:
            dependency_metrics["risk_level"] = "LOW"
            dependency_metrics["priority"] = "P3 - Monitor regularly"
        
        # Generate recommendations
        dependency_metrics["diversification_recommendations"] = self._recommend_diversification(
            indian_oem,
            dependency_metrics["china_dependency_score"]
        )
        
        return dependency_metrics
    
    def _calculate_dependency_score(self, oem: str) -> float:
        """
        Calculate dependency score based on network topology.
        
        Research Innovation: Weighted centrality considering transaction value & criticality
        """
        if not self.network.has_node(oem):
            return 0.0
        
        # Find all suppliers to this OEM
        suppliers = list(self.network.predecessors(oem))
        
        if not suppliers:
            return 0.0
        
        # Calculate weighted dependency
        total_value = 0
        china_value = 0
        
        for supplier in suppliers:
            edge_data = self.network.get_edge_data(supplier, oem)
            value = edge_data.get('value', 0)
            criticality = edge_data.get('criticality', 0.5)
            
            weighted_value = value * criticality
            total_value += weighted_value
            
            # Check if Chinese supplier
            supplier_country = self.network.nodes[supplier].get('country', '')
            if supplier_country == 'China':
                china_value += weighted_value
        
        # Dependency score = China's share of weighted value
        dependency_score = china_value / total_value if total_value > 0 else 0
        
        return round(dependency_score, 3)
    
    def _find_critical_suppliers(self, oem: str) -> List[Dict[str, Any]]:
        """
        Identify which Chinese suppliers are most critical.
        
        Research Innovation: Bottleneck identification using betweenness centrality
        """
        if not self.network.has_node(oem):
            return []
        
        critical_suppliers = []
        
        # Calculate betweenness centrality for the network
        try:
            centrality = nx.betweenness_centrality(self.network, weight='value')
        except:
            centrality = {}
        
        # Find Chinese suppliers to this OEM
        suppliers = list(self.network.predecessors(oem))
        
        for supplier in suppliers:
            supplier_country = self.network.nodes[supplier].get('country', '')
            
            if supplier_country == 'China':
                edge_data = self.network.get_edge_data(supplier, oem)
                
                critical_suppliers.append({
                    "supplier_name": supplier,
                    "component": edge_data.get('component', 'Unknown'),
                    "annual_value_inr": edge_data.get('value', 0),
                    "criticality": edge_data.get('criticality', 0.5),
                    "centrality_score": centrality.get(supplier, 0),
                    "bottleneck_risk": "HIGH" if centrality.get(supplier, 0) > 0.1 else "MEDIUM"
                })
        
        # Sort by criticality
        critical_suppliers.sort(key=lambda x: x['criticality'], reverse=True)
        
        return critical_suppliers
    
    def _find_alternatives(self, oem: str) -> List[Dict[str, str]]:
        """
        Identify alternative suppliers for diversification.
        
        Research Innovation: Alternative path finding in supply network
        """
        alternatives = []
        
        # Sample alternative suppliers (in real implementation, query database)
        alternative_countries = {
            "Lithium Battery": ["South Korea (LG Chem)", "Japan (Panasonic)", "Taiwan (CATL)"],
            "Electric Motor": "Germany (Bosch), India (Mahindra Electric)",
            "Power Electronics": ["Japan (Mitsubishi)", "USA (Tesla Suppliers)", "India (Sona BLW)"],
            "Charging Systems": ["Europe (ABB)", "India (Exicom)", "USA (ChargePoint)"]
        }
        
        # Get components from Chinese suppliers
        if self.network and self.network.has_node(oem):
            suppliers = list(self.network.predecessors(oem))
            
            for supplier in suppliers:
                supplier_country = self.network.nodes[supplier].get('country', '')
                
                if supplier_country == 'China':
                    edge_data = self.network.get_edge_data(supplier, oem)
                    component = edge_data.get('component', 'Unknown')
                    
                    alts = alternative_countries.get(component, ["India (Domestic)", "ASEAN countries"])
                    
                    for alt in alts:
                        alternatives.append({
                            "current_supplier": supplier,
                            "component": component,
                            "alternative_supplier": alt,
                            "transition_difficulty": "Medium",
                            "timeline": "12-18 months"
                        })
        
        return alternatives[:10]  # Top 10 alternatives
    
    def _recommend_diversification(self, oem: str, dependency_score: float) -> List[str]:
        """
        Generate strategic recommendations for supply chain diversification.
        
        Research Innovation: Risk-based diversification strategy
        """
        recommendations = []
        
        if dependency_score > 0.7:
            recommendations.extend([
                "URGENT: Reduce China dependency from {:.0%} to <40% within 24 months".format(dependency_score),
                "Establish dual-sourcing for all critical components (battery, motors, electronics)",
                "Partner with Korean (LG, Samsung) and Japanese (Panasonic) suppliers",
                "Invest in domestic Indian battery manufacturing (PLI scheme)",
                "Create strategic reserves of critical components (6-month buffer)"
            ])
        elif dependency_score > 0.4:
            recommendations.extend([
                "Moderate risk: Reduce dependency from {:.0%} to <30% over 36 months".format(dependency_score),
                "Develop secondary suppliers in ASEAN countries",
                "Invest in R&D for component localization",
                "Negotiate longer-term contracts with Chinese suppliers while diversifying"
            ])
        else:
            recommendations.extend([
                "Low risk: Maintain current diversification strategy",
                "Continue monitoring for geopolitical risks",
                "Incrementally increase domestic sourcing to 50%"
            ])
        
        return recommendations
    
    def simulate_disruption(self, disruption_scenario: str) -> Dict[str, Any]:
        """
        Simulate impact of supply chain disruption.
        
        Research Innovation: War-gaming supply shocks for preparedness
        
        Args:
            disruption_scenario: Type of disruption
                - "china_trade_war": All Chinese suppliers blocked
                - "rare_earth_embargo": Rare earth material shortage
                - "battery_shortage": Global battery supply crisis
                
        Returns:
            Impact assessment and recovery strategy
        """
        if not NETWORKX_AVAILABLE:
            return self._simplified_disruption_analysis(disruption_scenario)
        
        # Define disruption scenarios
        disruptions = {
            "china_trade_war": self.china_suppliers,
            "rare_earth_embargo": [s for s in self.china_suppliers if 'Battery' in s or 'Motor' in s],
            "battery_shortage": [s for s in self.network.nodes() if 'Battery' in s]
        }
        
        removed_nodes = disruptions.get(disruption_scenario, [])
        
        # Create copy of network and remove disrupted suppliers
        temp_network = self.network.copy()
        temp_network.remove_nodes_from(removed_nodes)
        
        # Measure impact
        original_edges = self.network.number_of_edges()
        disrupted_edges = temp_network.number_of_edges()
        
        impact_pct = ((original_edges - disrupted_edges) / original_edges) * 100 if original_edges > 0 else 0
        
        # Identify affected OEMs
        affected_oems = []
        for oem in self.indian_oems:
            if temp_network.has_node(oem):
                remaining_suppliers = list(temp_network.predecessors(oem))
                original_suppliers = list(self.network.predecessors(oem))
                
                if len(remaining_suppliers) < len(original_suppliers):
                    affected_oems.append({
                        "oem": oem,
                        "suppliers_lost": len(original_suppliers) - len(remaining_suppliers),
                        "production_impact": f"{((len(original_suppliers) - len(remaining_suppliers)) / len(original_suppliers)) * 100:.0f}%"
                    })
        
        return {
            "scenario": disruption_scenario,
            "disrupted_suppliers": len(removed_nodes),
            "supply_chain_impact": f"{impact_pct:.1f}%",
            "affected_oems": affected_oems,
            "recovery_timeline": self._estimate_recovery_time(impact_pct),
            "mitigation_strategy": self._generate_mitigation_strategy(disruption_scenario, impact_pct)
        }
    
    def _estimate_recovery_time(self, impact_pct: float) -> str:
        """Estimate time to recover from disruption"""
        if impact_pct > 50:
            return "24-36 months (Severe disruption)"
        elif impact_pct > 25:
            return "12-24 months (Major disruption)"
        elif impact_pct > 10:
            return "6-12 months (Moderate disruption)"
        else:
            return "3-6 months (Minor disruption)"
    
    def _generate_mitigation_strategy(self, scenario: str, impact: float) -> List[str]:
        """Generate mitigation strategy for disruption"""
        strategies = []
        
        if "china" in scenario.lower():
            strategies.extend([
                "Activate pre-qualified alternative suppliers in Korea, Japan, Taiwan",
                "Use strategic component reserves (if available)",
                "Collaborate with government for emergency import facilitation",
                "Accelerate domestic manufacturing under PLI scheme"
            ])
        
        if "battery" in scenario.lower():
            strategies.extend([
                "Shift to alternative battery chemistries (LFP → NMC or vice versa)",
                "Reduce vehicle production temporarily to preserve battery inventory",
                "Partner with Indian battery manufacturers (Reliance, Ola Electric)"
            ])
        
        if impact > 50:
            strategies.append("Consider temporary production halt for affected models")
        
        return strategies
    
    def _simplified_dependency_analysis(self, oem: str) -> Dict[str, Any]:
        """Fallback analysis when NetworkX not available"""
        return {
            "oem": oem,
            "china_dependency_score": 0.65,  # Estimated
            "risk_level": "HIGH",
            "note": "Simplified analysis - install NetworkX for detailed metrics",
            "recommendation": "Diversify supply chain to reduce China dependency"
        }
    
    def _simplified_disruption_analysis(self, scenario: str) -> Dict[str, Any]:
        """Fallback disruption analysis"""
        return {
            "scenario": scenario,
            "impact": "Moderate to High (35-50% supply chain disruption)",
            "note": "Simplified analysis - install NetworkX for detailed simulation",
            "recovery_timeline": "12-18 months"
        }
    
    def _build_simplified_network(self, data: List[Dict[str, Any]]) -> None:
        """Build simplified network structure when NetworkX unavailable"""
        for item in data:
            if item.get('supplier_country') == 'China':
                if item['supplier'] not in self.china_suppliers:
                    self.china_suppliers.append(item['supplier'])
            if item['oem'] not in self.indian_oems:
                self.indian_oems.append(item['oem'])
