"""
Test script for Chart Service

Quick test to verify chart generation is working correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chart_service import ChartService

def test_chart_generation():
    """Test all chart types."""
    
    print("🧪 Testing Chart Service...")
    print("-" * 50)
    
    # Sample data
    test_data = {
        'scenarios': ['Without Infrastructure', 'With Infrastructure'],
        'metrics': {
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
            }
        },
        'years': list(range(2024, 2031)),
        'growth_without_ports': [5, 8, 11, 14, 16, 18, 18],
        'growth_with_ports': [5, 10, 16, 22, 26, 29, 30],
        'labels': ['Domestic OEMs', 'Foreign OEMs', 'New Entrants'],
        'sizes': [40, 45, 15]
    }
    
    chart_service = ChartService()
    
    # Test Bar Chart
    print("\n✓ Generating Bar Chart...")
    try:
        bar_chart = chart_service.generate_comparison_chart(test_data, 'bar')
        print(f"  Bar chart generated: {len(bar_chart)} characters")
        print(f"  Preview: {bar_chart[:50]}...")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False
    
    # Test Line Chart
    print("\n✓ Generating Line Chart...")
    try:
        line_chart = chart_service.generate_comparison_chart(test_data, 'line')
        print(f"  Line chart generated: {len(line_chart)} characters")
        print(f"  Preview: {line_chart[:50]}...")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False
    
    # Test Pie Chart
    print("\n✓ Generating Pie Chart...")
    try:
        pie_chart = chart_service.generate_comparison_chart(test_data, 'pie')
        print(f"  Pie chart generated: {len(pie_chart)} characters")
        print(f"  Preview: {pie_chart[:50]}...")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All chart generation tests passed!")
    print("=" * 50)
    return True

if __name__ == '__main__':
    success = test_chart_generation()
    sys.exit(0 if success else 1)
