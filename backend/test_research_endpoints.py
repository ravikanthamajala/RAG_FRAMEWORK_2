"""
Test script for research novelty endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_explain_forecast():
    """Test the explainable AI endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Explain Forecast Endpoint")
    print("="*80)
    
    url = f"{BASE_URL}/explain-forecast"
    data = {
        "prediction": 28.5,
        "features": {
            "subsidy_amount": 75000,
            "charging_infrastructure": 8000,
            "battery_cost": 120000,
            "consumer_awareness": 60
        }
    }
    
    print(f"\n📤 Request to {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nExplanation:")
            print(json.dumps(result, indent=2))
            
            if 'explanation' in result:
                exp = result['explanation']
                print(f"\n🔍 Top Driver: {exp['top_drivers'][0]['factor']} ({exp['top_drivers'][0]['contribution_pct']}%)")
                print(f"🔮 Counterfactual: {exp['counterfactuals'][0]['scenario']}")
        else:
            print(f"❌ FAILED: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_analyze_supply_chain():
    """Test the supply chain network analysis endpoint"""
    print("\n" + "="*80)
    print("TEST 2: Analyze Supply Chain Endpoint")
    print("="*80)
    
    url = f"{BASE_URL}/analyze-supply-chain"
    data = {
        "oem_name": "Tata Motors"
        # Empty supply_chain_data will trigger sample data generation
    }
    
    print(f"\n📤 Request to {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nAnalysis:")
            print(json.dumps(result, indent=2))
            
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"\n🕸️ China Dependency Score: {analysis['china_dependency_score']}")
                print(f"⚠️ Risk Level: {analysis['risk_level']}")
                print(f"🏭 Critical Suppliers: {len(analysis['critical_suppliers'])}")
        else:
            print(f"❌ FAILED: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_simulate_disruption():
    """Test the disruption simulation endpoint"""
    print("\n" + "="*80)
    print("TEST 3: Simulate Disruption Endpoint")
    print("="*80)
    
    url = f"{BASE_URL}/simulate-disruption"
    data = {
        "scenario": "china_trade_war"
        # Empty supply_chain_data will trigger sample data
    }
    
    print(f"\n📤 Request to {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nSimulation:")
            print(json.dumps(result, indent=2))
            
            if 'simulation' in result:
                sim = result['simulation']
                print(f"\n💥 Scenario: {sim['scenario']}")
                print(f"📉 Impact: {sim['supply_chain_impact']}")
                print(f"⏱️ Recovery: {sim['recovery_timeline']}")
        else:
            print(f"❌ FAILED: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_explain_policy():
    """Test the policy explanation endpoint"""
    print("\n" + "="*80)
    print("TEST 4: Explain Policy Endpoint")
    print("="*80)
    
    url = f"{BASE_URL}/explain-policy"
    data = {
        "policy": "EV Purchase Subsidy",
        "impact_score": 0.85,
        "supporting_data": {
            "china_success_rate": 78,
            "cost_effectiveness": 120000,
            "market_readiness": 7.5
        }
    }
    
    print(f"\n📤 Request to {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nExplanation:")
            print(json.dumps(result, indent=2))
            
            if 'explanation' in result:
                exp = result['explanation']
                print(f"\n📋 Recommendation: {exp['recommendation']}")
                print(f"📊 Evidence: {exp['evidence'][0]}")
                print(f"🎯 Priority: {exp['implementation_priority']}")
        else:
            print(f"❌ FAILED: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + " "*20 + "RESEARCH NOVELTY ENDPOINTS TEST" + " "*27 + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    
    # Run all tests
    test_explain_forecast()
    test_analyze_supply_chain()
    test_simulate_disruption()
    test_explain_policy()
    
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + " "*28 + "TESTING COMPLETE" + " "*34 + "#")
    print("#" + " "*78 + "#")
    print("#"*80 + "\n")
