"""
Policy Visualization Generator
Creates visualizations for policy analysis, adoption timelines, and strategic roadmaps
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import base64
from typing import List, Dict, Any
from datetime import datetime

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8f9fa'

class PolicyVisualizer:
    """Generate policy analysis visualizations."""
    
    def __init__(self):
        """Initialize the visualizer."""
        self.colors = {
            'china': '#E74C3C',
            'india': '#3498DB',
            'adopted': '#2ECC71',
            'gap': '#F39C12',
            'high': '#27AE60',
            'medium': '#F39C12',
            'low': '#E74C3C'
        }
    
    def create_policy_adoption_timeline(self, policies: List[Dict]) -> str:
        """
        Create timeline visualization showing when India adopted policies from China.
        
        Args:
            policies: List of policy adoption data
            
        Returns:
            Base64 encoded PNG image
        """
        if not policies:
            return self._create_placeholder("No policy data available")
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Extract data
        policy_names = [p['policy_name'][:40] + '...' if len(p['policy_name']) > 40 else p['policy_name'] 
                       for p in policies]
        china_years = [p.get('china_year', 2000) for p in policies]
        india_years = [p.get('india_year', 2020) for p in policies]
        
        y_positions = np.arange(len(policies))
        
        # Plot timeline bars
        for i, (china_yr, india_yr) in enumerate(zip(china_years, india_years)):
            # China implementation
            ax.scatter(china_yr, i, color=self.colors['china'], s=200, zorder=3, 
                      marker='s', label='China' if i == 0 else '')
            # India adoption
            ax.scatter(india_yr, i, color=self.colors['india'], s=200, zorder=3,
                      marker='o', label='India' if i == 0 else '')
            # Connection line
            ax.plot([china_yr, india_yr], [i, i], color='gray', linewidth=2, 
                   alpha=0.5, linestyle='--', zorder=1)
            
            # Time gap annotation
            gap_years = india_yr - china_yr
            mid_year = (china_yr + india_yr) / 2
            ax.text(mid_year, i + 0.15, f'{gap_years}yr gap', 
                   ha='center', va='bottom', fontsize=9, color='#555',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # Styling
        ax.set_yticks(y_positions)
        ax.set_yticklabels(policy_names, fontsize=10)
        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_title('Policy Adoption Timeline: China → India', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(axis='x', alpha=0.3)
        
        # Add success level indicators
        for i, policy in enumerate(policies):
            success = policy.get('success_level', 'Medium')
            color = self.colors.get(success.lower(), self.colors['medium'])
            ax.scatter(india_years[i] + 0.5, i, marker='*', s=300, 
                      color=color, zorder=4, edgecolors='black', linewidth=0.5)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def create_contribution_waterfall(self, contributions: Dict[str, Dict]) -> str:
        """
        Create waterfall chart showing policy contributions to forecast.
        
        Args:
            contributions: Policy contribution breakdown
            
        Returns:
            Base64 encoded PNG image
        """
        if not contributions:
            return self._create_placeholder("No contribution data available")
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Extract data
        categories = []
        percentages = []
        descriptions = []
        
        for category, data in contributions.items():
            categories.append(category.replace('_', ' ').title())
            percentages.append(data.get('percentage', 0))
            descriptions.append(data.get('description', '')[:50])
        
        # Sort by percentage
        sorted_indices = np.argsort(percentages)[::-1]
        categories = [categories[i] for i in sorted_indices]
        percentages = [percentages[i] for i in sorted_indices]
        descriptions = [descriptions[i] for i in sorted_indices]
        
        # Calculate cumulative values for waterfall
        cumulative = np.cumsum([0] + percentages)
        
        # Create bars
        colors_list = plt.cm.viridis(np.linspace(0.3, 0.9, len(categories)))
        
        for i, (cat, pct, desc) in enumerate(zip(categories, percentages, descriptions)):
            ax.bar(i, pct, bottom=cumulative[i], color=colors_list[i], 
                  edgecolor='black', linewidth=1.5, alpha=0.85)
            
            # Value labels
            ax.text(i, cumulative[i] + pct/2, f'{pct}%', 
                   ha='center', va='center', fontweight='bold', 
                   fontsize=12, color='white' if pct > 5 else 'black')
            
            # Connecting lines
            if i < len(categories) - 1:
                ax.plot([i + 0.4, i + 0.6], [cumulative[i+1], cumulative[i+1]], 
                       color='gray', linestyle='--', linewidth=1, alpha=0.5)
        
        # Styling
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Contribution to Forecast (%)', fontsize=12, fontweight='bold')
        ax.set_title('Policy Contribution Breakdown to 2030 Forecast', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_ylim(0, cumulative[-1] * 1.1)
        
        # Total line
        ax.axhline(cumulative[-1], color='red', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(len(categories) - 0.5, cumulative[-1] + 1, 
               f'Total: {cumulative[-1]:.0f}%', 
               fontsize=12, fontweight='bold', color='red',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def create_strategic_roadmap(self, recommendations: List[Dict]) -> str:
        """
        Create strategic roadmap visualization with timeline and priorities.
        
        Args:
            recommendations: List of policy recommendations
            
        Returns:
            Base64 encoded PNG image
        """
        if not recommendations:
            return self._create_placeholder("No recommendations available")
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Parse timelines and priorities
        roadmap_data = []
        for rec in recommendations:
            timeline_str = rec.get('timeline', '2024-2025')
            priority = rec.get('priority', 'Medium')
            title = rec.get('title', 'Policy')
            impact = rec.get('impact', 'TBD')
            
            # Parse year range
            years = timeline_str.split('-')
            start_year = int(years[0]) if years else 2024
            end_year = int(years[1]) if len(years) > 1 else start_year + 1
            
            roadmap_data.append({
                'title': title,
                'start': start_year,
                'end': end_year,
                'priority': priority,
                'impact': impact
            })
        
        # Sort by start year and priority
        priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        roadmap_data.sort(key=lambda x: (x['start'], priority_order.get(x['priority'], 3)))
        
        # Create Gantt chart
        y_positions = np.arange(len(roadmap_data))
        
        for i, item in enumerate(roadmap_data):
            duration = item['end'] - item['start']
            priority = item['priority']
            
            # Color based on priority
            if 'Critical' in priority or 'High' in priority:
                color = self.colors['high']
            elif 'Medium' in priority:
                color = self.colors['medium']
            else:
                color = self.colors['low']
            
            # Draw bar
            ax.barh(i, duration, left=item['start'], height=0.6, 
                   color=color, edgecolor='black', linewidth=1.5, alpha=0.8)
            
            # Add title
            title_text = item['title'][:45] + '...' if len(item['title']) > 45 else item['title']
            ax.text(item['start'] - 0.3, i, title_text, 
                   ha='right', va='center', fontsize=9, fontweight='bold')
            
            # Add priority badge
            ax.text(item['start'] + duration/2, i, priority, 
                   ha='center', va='center', fontsize=8, color='white',
                   fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.7))
            
            # Add impact on the right
            impact_text = item['impact'][:40] + '...' if len(item['impact']) > 40 else item['impact']
            ax.text(item['end'] + 0.3, i, impact_text, 
                   ha='left', va='center', fontsize=8, style='italic', color='#555')
        
        # Styling
        ax.set_yticks([])
        ax.set_xlabel('Year', fontsize=14, fontweight='bold')
        ax.set_title('Strategic Policy Implementation Roadmap (2024-2030)', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlim(2023.5, 2031)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Add phase markers
        phases = [
            (2024, 2025, 'Short Term', '#E8F8F5'),
            (2026, 2028, 'Medium Term', '#FEF9E7'),
            (2029, 2030, 'Long Term', '#FADBD8')
        ]
        
        for start, end, label, color in phases:
            ax.axvspan(start, end, alpha=0.15, color=color)
            ax.text((start + end) / 2, len(roadmap_data), label, 
                   ha='center', va='bottom', fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.7))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def create_policy_gap_analysis(self, gaps: List[str], adopted: List[Dict]) -> str:
        """
        Create visualization showing policy gaps vs adopted policies.
        
        Args:
            gaps: List of policy gaps
            adopted: List of adopted policies
            
        Returns:
            Base64 encoded PNG image
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left: Gap analysis
        gap_count = len(gaps)
        adopted_count = len(adopted)
        
        categories = ['Policy Gaps', 'Policies Adopted\nfrom China']
        values = [gap_count, adopted_count]
        colors_bar = [self.colors['gap'], self.colors['adopted']]
        
        bars = ax1.bar(categories, values, color=colors_bar, edgecolor='black', linewidth=2)
        ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax1.set_title('Policy Status Overview', fontsize=14, fontweight='bold')
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(val)}',
                    ha='center', va='bottom', fontsize=16, fontweight='bold')
        
        # Right: Top gaps
        if gaps:
            top_gaps = gaps[:8]  # Show top 8
            y_pos = np.arange(len(top_gaps))
            
            gap_labels = [g[:60] + '...' if len(g) > 60 else g for g in top_gaps]
            
            ax2.barh(y_pos, [1] * len(top_gaps), color=self.colors['gap'], 
                    edgecolor='black', linewidth=1, alpha=0.7)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(gap_labels, fontsize=9)
            ax2.set_xlabel('Priority', fontsize=12, fontweight='bold')
            ax2.set_title('Key Policy Gaps to Address', fontsize=14, fontweight='bold')
            ax2.set_xlim(0, 1.2)
            ax2.set_xticks([])
            
            # Add priority indicators
            for i in range(len(top_gaps)):
                priority_level = 'High' if i < 3 else 'Medium'
                color = self.colors['high'] if i < 3 else self.colors['medium']
                ax2.text(0.5, i, priority_level, ha='center', va='center',
                        color='white', fontweight='bold', fontsize=10,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=color))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
    
    def _create_placeholder(self, message: str) -> str:
        """Create placeholder image with message."""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center',
               fontsize=16, fontweight='bold', color='#555')
        ax.axis('off')
        return self._fig_to_base64(fig)
