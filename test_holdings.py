#!/usr/bin/env python3
import requests
import json

# Force create demo holdings for your wallet
wallet_address = "0xa705bfe8e754722d4afa26f46f8ea0fbb94535d1"
base_url = "http://localhost:8000/api/v1"

print("🧪 Testing Portfolio with Demo Holdings Creation")
print("=" * 50)

try:
    # First, seed the database to ensure bonds exist
    print("1. 🌱 Seeding database...")
    seed_response = requests.post(f"{base_url}/admin/seed-data", timeout=10)
    print(f"   Status: {seed_response.status_code}")
    
    # Force create demo holdings
    print(f"\n2. 🏗️ Creating demo holdings for {wallet_address}...")
    demo_response = requests.post(f"{base_url}/portfolio/{wallet_address}/demo-holdings", timeout=10)
    print(f"   Status: {demo_response.status_code}")
    if demo_response.status_code == 200:
        result = demo_response.json()
        print(f"   Message: {result.get('message', 'Unknown')}")
        if 'portfolio' in result:
            portfolio = result['portfolio']
            print(f"   Holdings Count: {portfolio.get('holdings_count', 0)}")
            print(f"   Total Value: ${portfolio.get('total_portfolio_value', 0)}")
    
    # Check the regular portfolio endpoint
    print(f"\n3. 💼 Checking portfolio endpoint...")
    portfolio_response = requests.get(f"{base_url}/portfolio/{wallet_address}", timeout=10)
    print(f"   Status: {portfolio_response.status_code}")
    if portfolio_response.status_code == 200:
        portfolio = portfolio_response.json()
        print(f"   Holdings Count: {portfolio.get('holdings_count', 0)}")
        print(f"   Total Value: ${portfolio.get('total_portfolio_value', 0)}")
        print(f"   Holdings: {len(portfolio.get('holdings', []))}")
        
        for holding in portfolio.get('holdings', []):
            print(f"     - {holding['bond_name']}: {holding['quantity']} units @ ${holding['current_price']}")
    else:
        print(f"   Error: {portfolio_response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend server. Is it running on port 8000?")
except requests.exceptions.Timeout:
    print("❌ Request timed out. Server might be slow to respond.")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("Test completed!")
