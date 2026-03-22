"""
Chart Generation Service for Automotive Market Analysis

Generates comparison charts for India's automotive market projections,
including scenarios with and without infrastructure development.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server environments
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List, Any
import numpy as np


class ChartService:
    """Service for generating comparison and analysis charts."""
    
    @staticmethod
    def generate_comparison_chart(data: Dict[str, Any], chart_type: str = 'bar') -> str:
        """
        Generate chart comparing different scenarios.
        
        Args:
            data: Dictionary containing comparison data with structure:
                  {
                      'scenarios': ['Scenario 1', 'Scenario 2'],
                      'metrics': {
                          'Metric Name': {
                              'without_ports': value1,
                              'with_ports': value2
                          }
                      }
                  }
            chart_type: Type of chart ('bar', 'line', 'pie')
            
        Returns:
            Base64 encoded image string with data URI prefix
        """
        plt.clf()  # Clear any existing plots
        plt.figure(figsize=(12, 7))
        
        if chart_type == 'bar':
            return ChartService._generate_bar_chart(data)
        elif chart_type == 'line':
            return ChartService._generate_line_chart(data)
        elif chart_type == 'pie':
            return ChartService._generate_pie_chart(data)
        
        return ""
    
    @staticmethod
    def _generate_bar_chart(data: Dict[str, Any]) -> str:
        """Generate bar chart for scenario comparison."""
        metrics = data.get('metrics', {})
        
        if not metrics:
            # Return empty chart if no data
            plt.text(0.5, 0.5, 'No comparison data available', 
                    ha='center', va='center', fontsize=14)
            return ChartService._convert_plot_to_base64()
        
        categories = list(metrics.keys())
        values_without = [metrics[cat].get('without_ports', 0) for cat in categories]
        values_with = [metrics[cat].get('with_ports', 0) for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        # Create bars with attractive colors
        bars1 = plt.bar([i - width/2 for i in x], values_without, width, 
                        label='Without Infrastructure', color='#FF6B6B', alpha=0.8)
        bars2 = plt.bar([i + width/2 for i in x], values_with, width, 
                        label='With Infrastructure', color='#4ECDC4', alpha=0.8)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.xlabel('Metrics', fontsize=12, fontweight='bold')
        plt.ylabel('Values', fontsize=12, fontweight='bold')
        plt.title('India 2030 Growth Comparison: Infrastructure Impact on Automotive Market', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.xticks(x, categories, rotation=45, ha='right')
        plt.legend(loc='upper left', fontsize=10)
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        return ChartService._convert_plot_to_base64()
    
    @staticmethod
    def _generate_line_chart(data: Dict[str, Any]) -> str:
        """Generate line chart for trend comparison over time."""
        years = data.get('years', list(range(2024, 2031)))
        growth_without = data.get('growth_without_ports', [])
        growth_with = data.get('growth_with_ports', [])
        
        if not growth_without or not growth_with:
            plt.text(0.5, 0.5, 'No trend data available', 
                    ha='center', va='center', fontsize=14)
            return ChartService._convert_plot_to_base64()
        
        plt.plot(years, growth_without, marker='o', markersize=8, 
                label='Without Infrastructure', color='#FF6B6B', linewidth=3)
        plt.plot(years, growth_with, marker='s', markersize=8, 
                label='With Infrastructure', color='#4ECDC4', linewidth=3)
        
        # Add data point labels
        for i, (year, val1, val2) in enumerate(zip(years, growth_without, growth_with)):
            if i % 2 == 0:  # Label every other point to avoid crowding
                plt.text(year, val1, f'{val1:.1f}%', fontsize=8, ha='center', va='bottom')
                plt.text(year, val2, f'{val2:.1f}%', fontsize=8, ha='center', va='bottom')
        
        plt.xlabel('Year', fontsize=12, fontweight='bold')
        plt.ylabel('EV Adoption Rate (%)', fontsize=12, fontweight='bold')
        plt.title('Projected EV Market Growth in India (2024-2030)', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.legend(loc='upper left', fontsize=10)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.xticks(years)
        plt.tight_layout()
        
        return ChartService._convert_plot_to_base64()
    
    @staticmethod
    def _generate_pie_chart(data: Dict[str, Any]) -> str:
        """Generate pie chart for market distribution."""
        labels = data.get('labels', ['Domestic OEMs', 'Foreign OEMs', 'New Entrants'])
        sizes = data.get('sizes', [40, 45, 15])
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
        
        # Create pie chart with explosion for emphasis
        explode = [0.05] * len(sizes)  # Slightly separate all slices
        
        plt.pie(sizes, labels=labels, colors=colors[:len(sizes)], autopct='%1.1f%%', 
               startangle=90, explode=explode, shadow=True,
               textprops={'fontsize': 11, 'fontweight': 'bold'})
        plt.title('Projected OEM Market Share 2030\n(With Infrastructure Development)', 
                 fontsize=14, fontweight='bold', pad=20)
        plt.axis('equal')
        plt.tight_layout()
        
        return ChartService._convert_plot_to_base64()
    
    @staticmethod
    def _convert_plot_to_base64() -> str:
        """Convert matplotlib plot to base64 encoded string."""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close('all')  # Close all figures to free memory
        return f"data:image/png;base64,{image_base64}"
    
    @staticmethod
    def extract_metrics_from_text(text: str) -> Dict[str, Any]:
        """
        Extract numerical metrics from RAG response text.
        
        This is a simplified version - in production, you would use
        more sophisticated NLP techniques or structured data extraction.
        
        Args:
            text: RAG agent response text
            
        Returns:
            Dictionary with extracted metrics
        """
        # Example default metrics based on common automotive market analysis
        # In production, parse these from the actual response text
        default_metrics = {
            'EV Adoption Rate (%)': {
                'without_ports': 18.0,
                'with_ports': 30.0
            },
            'GDP Growth (%)': {
                'without_ports': 6.5,
                'with_ports': 7.8
            },
            'Jobs Created (K)': {
                'without_ports': 150,
                'with_ports': 320
            },
            'Foreign Investment ($B)': {
                'without_ports': 5.2,
                'with_ports': 12.5
            }
        }
        
        # Default trend data for line charts
        trend_data = {
            'years': list(range(2024, 2031)),
            'growth_without_ports': [5, 8, 11, 14, 16, 18, 18],
            'growth_with_ports': [5, 10, 16, 22, 26, 29, 30]
        }
        
        # Default distribution data for pie charts
        distribution_data = {
            'labels': ['Domestic OEMs', 'Foreign OEMs', 'New Entrants', 'Joint Ventures'],
            'sizes': [35, 40, 15, 10]
        }
        
        return {
            'scenarios': ['Without Infrastructure', 'With Infrastructure'],
            'metrics': default_metrics,
            **trend_data,
            **distribution_data
        }
