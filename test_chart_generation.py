"""
Quick test to check if charts are being generated
"""
import requests
import json

# Test with a forecast query (should generate charts)
test_queries = [
    "What will be the EV market growth in India by 2030?",
    "Compare India's automotive growth with and without infrastructure",
    "What is the market share distribution of OEMs?"
]

print("="*70)
print("TESTING CHART GENERATION")
print("="*70)
print()

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print("-" * 70)
    
    try:
        response = requests.post(
            'http://localhost:4000/api/query-with-charts',
            json={'query': query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: SUCCESS")
            print(f"   Has visualization: {data.get('has_visualization', False)}")
            print(f"   Number of charts: {len(data.get('charts', []))}")
            
            if data.get('charts'):
                for i, chart in enumerate(data['charts'], 1):
                    print(f"   Chart {i}: {chart.get('type')} - {chart.get('title')}")
                    # Check if image data exists
                    if chart.get('image'):
                        img_data = chart['image']
                        if img_data.startswith('data:image'):
                            print(f"            ✅ Image data present (length: {len(img_data)} chars)")
                        else:
                            print(f"            ❌ Image data format incorrect")
                    else:
                        print(f"            ❌ No image data")
            else:
                print("   ⚠️  No charts generated!")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend. Is the server running?")
        print("   Run: cd backend && python run.py")
        break
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

print()
print("="*70)
print("Test complete!")
print("="*70)
