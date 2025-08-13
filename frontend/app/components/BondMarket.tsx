"use client";

import { useState, useEffect } from "react";

interface Bond {
  id: string;
  name: string;
  isin: string;
  couponRate: number;
  faceValue: number;
  currentPrice: number;
  maturityDate: string;
  issuer: string;
  minUnit: number;
  yield: number;
}

export function BondMarket() {
  const [bonds, setBonds] = useState<Bond[]>([]);
  const [selectedBond, setSelectedBond] = useState<Bond | null>(null);

  useEffect(() => {
    // Mock bond data
    setBonds([
      {
        id: "1",
        name: "HDFC Infrastructure Bond",
        isin: "INE001A01001",
        couponRate: 7.5,
        faceValue: 1000,
        currentPrice: 1025,
        maturityDate: "2027-12-31",
        issuer: "HDFC Ltd",
        minUnit: 100,
        yield: 7.2
      },
      {
        id: "2",
        name: "ICICI Corporate Bond",
        isin: "INE002A01002",
        couponRate: 8.2,
        faceValue: 1000,
        currentPrice: 1015,
        maturityDate: "2026-06-30",
        issuer: "ICICI Bank",
        minUnit: 50,
        yield: 8.0
      },
      {
        id: "3",
        name: "SBI Green Bond",
        isin: "INE003A01003",
        couponRate: 6.8,
        faceValue: 1000,
        currentPrice: 995,
        maturityDate: "2029-03-31",
        issuer: "State Bank of India",
        minUnit: 25,
        yield: 6.9
      }
    ]);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Bond Market</h2>
        <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
          + List New Bond
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <div className="flex flex-wrap gap-4">
          <select className="px-3 py-2 border rounded-md">
            <option>All Issuers</option>
            <option>Banks</option>
            <option>NBFCs</option>
            <option>Corporates</option>
          </select>
          <select className="px-3 py-2 border rounded-md">
            <option>All Maturities</option>
            <option>1-3 Years</option>
            <option>3-5 Years</option>
            <option>5+ Years</option>
          </select>
          <input
            type="text"
            placeholder="Search bonds..."
            className="px-3 py-2 border rounded-md flex-1 min-w-[200px]"
          />
        </div>
      </div>

      {/* Bond List */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bond
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Coupon
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Yield
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Maturity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Min Unit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bonds.map((bond) => (
                <tr key={bond.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{bond.name}</div>
                      <div className="text-sm text-gray-500">{bond.isin}</div>
                      <div className="text-xs text-gray-400">{bond.issuer}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {bond.couponRate}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ₹{bond.currentPrice}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {bond.yield}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(bond.maturityDate).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {bond.minUnit} units
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => setSelectedBond(bond)}
                      className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Trade
                    </button>
                    <button className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700">
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bond Details Modal */}
      {selectedBond && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Bond Details</h3>
              <button
                onClick={() => setSelectedBond(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <p className="font-medium">{selectedBond.name}</p>
                <p className="text-sm text-gray-600">{selectedBond.isin}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Coupon Rate</p>
                  <p className="font-medium">{selectedBond.couponRate}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Current Yield</p>
                  <p className="font-medium">{selectedBond.yield}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Face Value</p>
                  <p className="font-medium">₹{selectedBond.faceValue}</p>
                </div>
                <div>
                  <p className="text-gray-600">Current Price</p>
                  <p className="font-medium">₹{selectedBond.currentPrice}</p>
                </div>
              </div>
              <div className="flex space-x-2 pt-4">
                <button className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                  Buy
                </button>
                <button className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
                  Sell
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
