#!/usr/bin/env python3
import requests
import json

# Test the portfolio API
wallet_address = "0xa705bfe8e754722d4afa26f46f8ea0fbb94535d1"
base_url = "http://localhost:8000/api/v1"

try:
    # First, seed the database
    print("🌱 Seeding database...")
    seed_response = requests.post(f"{base_url}/admin/seed-data")
    print(f"Seed response: {seed_response.status_code}")
    if seed_response.status_code == 200:
        print(f"Seed data: {json.dumps(seed_response.json(), indent=2)}")
    
    # Check available bonds
    print("\n📋 Checking available bonds...")
    bonds_response = requests.get(f"{base_url}/bonds/")
    print(f"Bonds response: {bonds_response.status_code}")
    if bonds_response.status_code == 200:
        bonds = bonds_response.json()
        print(f"Available bonds: {len(bonds)}")
        for bond in bonds:
            print(f"  - {bond['name']} (ID: {bond['id']})")
    
    # Check portfolio
    print(f"\n💼 Checking portfolio for wallet: {wallet_address}")
    portfolio_response = requests.get(f"{base_url}/portfolio/{wallet_address}")
    print(f"Portfolio response: {portfolio_response.status_code}")
    if portfolio_response.status_code == 200:
        portfolio = portfolio_response.json()
        print(f"Portfolio data: {json.dumps(portfolio, indent=2)}")
    else:
        print(f"Portfolio error: {portfolio_response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend server. Is it running on port 8000?")
except Exception as e:
    print(f"❌ Error: {e}")
