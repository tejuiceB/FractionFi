"use client";

import { useState, useEffect } from "react";

interface Holding {
  id: string;
  bond: string;
  isin: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  marketValue: number;
  pnl: number;
  pnlPercent: number;
}

export function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [totalPnL, setTotalPnL] = useState(0);

  useEffect(() => {
    // Mock portfolio data
    const mockHoldings = [
      {
        id: "1",
        bond: "HDFC Infrastructure Bond",
        isin: "INE001A01001",
        quantity: 100,
        avgPrice: 1020,
        currentPrice: 1025,
        marketValue: 102500,
        pnl: 500,
        pnlPercent: 0.49
      },
      {
        id: "2",
        bond: "ICICI Corporate Bond",
        isin: "INE002A01002",
        quantity: 50,
        avgPrice: 1010,
        currentPrice: 1015,
        marketValue: 50750,
        pnl: 250,
        pnlPercent: 0.50
      },
      {
        id: "3",
        bond: "SBI Green Bond",
        isin: "INE003A01003",
        quantity: 200,
        avgPrice: 1000,
        currentPrice: 995,
        marketValue: 199000,
        pnl: -1000,
        pnlPercent: -0.50
      }
    ];

    setHoldings(mockHoldings);
    setTotalValue(mockHoldings.reduce((sum, holding) => sum + holding.marketValue, 0));
    setTotalPnL(mockHoldings.reduce((sum, holding) => sum + holding.pnl, 0));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Portfolio</h2>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Portfolio Value</p>
              <p className="text-2xl font-bold text-gray-900">₹{totalValue.toLocaleString()}</p>
            </div>
            <div className="text-3xl">💼</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total P&L</p>
              <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalPnL >= 0 ? '+' : ''}₹{totalPnL.toLocaleString()}
              </p>
            </div>
            <div className="text-3xl">{totalPnL >= 0 ? '📈' : '📉'}</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Number of Holdings</p>
              <p className="text-2xl font-bold text-gray-900">{holdings.length}</p>
            </div>
            <div className="text-3xl">🏦</div>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">Holdings</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bond
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {holdings.map((holding) => (
                <tr key={holding.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{holding.bond}</div>
                      <div className="text-sm text-gray-500">{holding.isin}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {holding.quantity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ₹{holding.avgPrice}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ₹{holding.currentPrice}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ₹{holding.marketValue.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${holding.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {holding.pnl >= 0 ? '+' : ''}₹{holding.pnl.toLocaleString()}
                    </div>
                    <div className={`text-xs ${holding.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      ({holding.pnlPercent >= 0 ? '+' : ''}{(holding.pnlPercent || 0).toFixed(2)}%)
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
                      Buy More
                    </button>
                    <button className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">
                      Sell
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Portfolio Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Portfolio Allocation</h3>
          <div className="space-y-3">
            {holdings.map((holding) => {
              const percentage = (holding.marketValue / totalValue) * 100;
              return (
                <div key={holding.id}>
                  <div className="flex justify-between text-sm mb-1">
                    <span>{holding.bond}</span>
                    <span>{(percentage || 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Recent Transactions</h3>
          <div className="space-y-3">
            {[
              { type: "Buy", bond: "HDFC Infrastructure", amount: "₹50,000", date: "2025-08-12" },
              { type: "Sell", bond: "ICICI Corporate", amount: "₹25,000", date: "2025-08-11" },
              { type: "Buy", bond: "SBI Green Bond", amount: "₹75,000", date: "2025-08-10" },
            ].map((txn, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium text-sm">{txn.bond}</p>
                  <p className="text-xs text-gray-600">{txn.date}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-sm">{txn.amount}</p>
                  <p className={`text-xs ${txn.type === 'Buy' ? 'text-green-600' : 'text-red-600'}`}>
                    {txn.type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
