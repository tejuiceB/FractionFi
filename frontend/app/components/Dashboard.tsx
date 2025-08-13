"use client";

import { useState, useEffect } from "react";

export function Dashboard() {
  const [stats, setStats] = useState({
    totalBonds: 0,
    totalVolume: 0,
    activeOrders: 0,
    portfolioValue: 0
  });

  useEffect(() => {
    // Fetch dashboard stats from API
    fetch("http://localhost:8000/api/v1/bonds/")
      .then(res => res.json())
      .then(data => {
        // Mock data for now
        setStats({
          totalBonds: 5,
          totalVolume: 1250000,
          activeOrders: 23,
          portfolioValue: 45000
        });
      })
      .catch(err => console.log("API not available, using mock data"));
  }, []);

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">Welcome to FractionFi</h1>
        <p className="text-blue-100">Trade tokenized bonds with enhanced liquidity and fractional ownership</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Bonds</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalBonds}</p>
            </div>
            <div className="text-3xl">🏦</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Volume</p>
              <p className="text-2xl font-bold text-gray-900">${stats.totalVolume.toLocaleString()}</p>
            </div>
            <div className="text-3xl">💰</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Active Orders</p>
              <p className="text-2xl font-bold text-gray-900">{stats.activeOrders}</p>
            </div>
            <div className="text-3xl">📈</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Portfolio Value</p>
              <p className="text-2xl font-bold text-gray-900">${stats.portfolioValue.toLocaleString()}</p>
            </div>
            <div className="text-3xl">💼</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Recent Trades</h3>
          <div className="space-y-3">
            {[
              { bond: "HDFC 7.5% 2027", amount: "₹50,000", type: "Buy", time: "2 hours ago" },
              { bond: "ICICI 8.2% 2026", amount: "₹25,000", type: "Sell", time: "4 hours ago" },
              { bond: "SBI 6.8% 2029", amount: "₹75,000", type: "Buy", time: "1 day ago" },
            ].map((trade, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium">{trade.bond}</p>
                  <p className="text-sm text-gray-600">{trade.time}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{trade.amount}</p>
                  <p className={`text-sm ${trade.type === 'Buy' ? 'text-green-600' : 'text-red-600'}`}>
                    {trade.type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Market Updates</h3>
          <div className="space-y-3">
            {[
              { title: "New Bond Listing", desc: "HDFC Infrastructure Bond now available", time: "1 hour ago" },
              { title: "Rate Change", desc: "RBI repo rate increased by 0.25%", time: "3 hours ago" },
              { title: "Platform Update", desc: "New fractional trading features added", time: "1 day ago" },
            ].map((update, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded">
                <p className="font-medium">{update.title}</p>
                <p className="text-sm text-gray-600">{update.desc}</p>
                <p className="text-xs text-gray-500 mt-1">{update.time}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
