import requests
import json

print("\n" + "="*70)
print("  INDIA 2030 AUTOMOTIVE FORECAST - API TEST")
print("="*70 + "\n")

try:
    print("🔄 Requesting forecast from API...")
    response = requests.get('http://localhost:5000/api/forecast/india-2030', timeout=30)
    
    print(f"📡 Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ " + data['message'])
        print(f"📊 Charts Generated: {data['charts']['charts_generated']}\n")
        
        print("="*70)
        print("  2030 FORECAST COMPARISON")
        print("="*70)
        
        with_policies = data['report']['scenarios']['with_china_policies']
        without_policies = data['report']['scenarios']['without_china_policies']
        impact = data['report']['policy_impact']
        
        print("\n🟢 WITH CHINA POLICIES (Aggressive Transition):")
        print(f"   EV Units:        {with_policies['2030_ev_units']:.2f} Million")
        print(f"   Market Share:    {with_policies['2030_ev_percentage']:.1f}%")
        print(f"   Total Sales:     {with_policies['2030_total_sales']:.2f} Million")
        print(f"   EV CAGR:         {with_policies['cagr_ev']:.1f}%")
        print(f"   Cumulative EVs:  {with_policies['cumulative_evs_2024_2030']:.2f} Million")
        
        print("\n🔴 WITHOUT CHINA POLICIES (Business as Usual):")
        print(f"   EV Units:        {without_policies['2030_ev_units']:.2f} Million")
        print(f"   Market Share:    {without_policies['2030_ev_percentage']:.1f}%")
        print(f"   Total Sales:     {without_policies['2030_total_sales']:.2f} Million")
        print(f"   EV CAGR:         {without_policies['cagr_ev']:.1f}%")
        print(f"   Cumulative EVs:  {without_policies['cumulative_evs_2024_2030']:.2f} Million")
        
        print("\n" + "="*70)
        print("  POLICY IMPACT SUMMARY")
        print("="*70)
        print(f"\n💡 Additional EV Units (2030):    +{impact['additional_ev_units_2030']:.2f} Million")
        print(f"📈 Percentage Increase:           +{impact['percentage_increase']:.1f}%")
        print(f"🎯 Market Share Gain:             +{impact['market_share_gain']:.1f}%")
        print(f"🔢 Cumulative Additional EVs:     +{impact['cumulative_additional_evs']:.2f} Million")
        
        print("\n" + "="*70)
        print("  VISUALIZATION CHARTS")
        print("="*70)
        print("\n📂 Open these URLs in your browser:\n")
        for i, url in enumerate(data['charts']['chart_urls'], 1):
            full_url = f"http://localhost:5000{url}"
            print(f"   {i}. {full_url}")
        
        print("\n" + "="*70)
        print("  KEY INSIGHTS")
        print("="*70 + "\n")
        for i, finding in enumerate(data['report']['key_findings'], 1):
            print(f"  {i}. {finding}")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
        
    else:
        print(f"❌ ERROR: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR: Backend is not running!")
    print("\n💡 Start the backend first:")
    print("   cd backend")
    print("   python run.py\n")
except Exception as e:
    print(f"❌ EXCEPTION: {str(e)}")
