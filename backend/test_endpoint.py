"""
Test the chart visualization endpoint
"""

import requests
import json

print("\n" + "="*60)
print("🧪 TESTING CHART VISUALIZATION ENDPOINT")
print("="*60 + "\n")

# Test data
query_data = {
    "query": "Compare India's EV market growth with and without charging port infrastructure by 2030"
}

print("📤 Sending request to: http://localhost:5000/api/query-with-charts")
print(f"📝 Query: {query_data['query']}\n")

try:
    response = requests.post(
        'http://localhost:5000/api/query-with-charts',
        json=query_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"📊 Response Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ SUCCESS! Endpoint is working!\n")
        print("="*60)
        print("RESPONSE STRUCTURE:")
        print("="*60)
        print(f"✓ Has 'response' key: {'response' in data}")
        print(f"✓ Has 'charts' key: {'charts' in data}")
        print(f"✓ Has 'has_visualization' key: {'has_visualization' in data}")
        print(f"\n✓ Number of charts: {len(data.get('charts', []))}")
        
        if data.get('charts'):
            print(f"\n📊 CHARTS GENERATED:")
            for i, chart in enumerate(data['charts'], 1):
                print(f"  {i}. {chart.get('title', 'Untitled')} ({chart.get('type', 'unknown')} chart)")
                image_length = len(chart.get('image', ''))
                print(f"     Image size: {image_length:,} characters")
        
        print(f"\n📝 TEXT RESPONSE LENGTH: {len(data.get('response', ''))} characters")
        print(f"    Preview: {data.get('response', '')[:100]}...")
        
        print("\n" + "="*60)
        print("✅ CHART VISUALIZATION IS WORKING!")
        print("="*60)
        
    else:
        print(f"❌ ERROR: Status code {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to Flask server")
    print("   Make sure the server is running on http://localhost:5000")
    print("   Run: python run.py")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n")
