"use client";

import { useState } from "react";

interface Order {
  id: string;
  type: "buy" | "sell";
  bond: string;
  quantity: number;
  price: number;
  status: "open" | "filled" | "partial" | "cancelled";
  timestamp: string;
}

export function Trading() {
  const [orderType, setOrderType] = useState<"buy" | "sell">("buy");
  const [orderForm, setOrderForm] = useState({
    bond: "",
    quantity: "",
    price: "",
    orderType: "limit"
  });

  const [orders] = useState<Order[]>([
    {
      id: "1",
      type: "buy",
      bond: "HDFC Infrastructure Bond",
      quantity: 100,
      price: 1025,
      status: "open",
      timestamp: "2025-08-13T10:30:00Z"
    },
    {
      id: "2",
      type: "sell",
      bond: "ICICI Corporate Bond",
      quantity: 50,
      price: 1015,
      status: "filled",
      timestamp: "2025-08-13T09:15:00Z"
    }
  ]);

  const handleSubmitOrder = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Submitting order:", { ...orderForm, type: orderType });
    // Here you would call your API
    alert("Order submitted successfully!");
    setOrderForm({ bond: "", quantity: "", price: "", orderType: "limit" });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Trading</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Order Form */}
        <div className="lg:col-span-1">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">Place Order</h3>
            
            {/* Buy/Sell Toggle */}
            <div className="flex mb-4">
              <button
                onClick={() => setOrderType("buy")}
                className={`flex-1 py-2 px-4 rounded-l-md font-medium ${
                  orderType === "buy"
                    ? "bg-green-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Buy
              </button>
              <button
                onClick={() => setOrderType("sell")}
                className={`flex-1 py-2 px-4 rounded-r-md font-medium ${
                  orderType === "sell"
                    ? "bg-red-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Sell
              </button>
            </div>

            <form onSubmit={handleSubmitOrder} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bond
                </label>
                <select
                  value={orderForm.bond}
                  onChange={(e) => setOrderForm({ ...orderForm, bond: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a bond</option>
                  <option value="hdfc-infra">HDFC Infrastructure Bond</option>
                  <option value="icici-corp">ICICI Corporate Bond</option>
                  <option value="sbi-green">SBI Green Bond</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Order Type
                </label>
                <select
                  value={orderForm.orderType}
                  onChange={(e) => setOrderForm({ ...orderForm, orderType: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="limit">Limit Order</option>
                  <option value="market">Market Order</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity (Units)
                </label>
                <input
                  type="number"
                  value={orderForm.quantity}
                  onChange={(e) => setOrderForm({ ...orderForm, quantity: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter quantity"
                  min="1"
                  required
                />
              </div>

              {orderForm.orderType === "limit" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price (₹)
                  </label>
                  <input
                    type="number"
                    value={orderForm.price}
                    onChange={(e) => setOrderForm({ ...orderForm, price: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter price"
                    step="0.01"
                    required
                  />
                </div>
              )}

              <button
                type="submit"
                className={`w-full py-2 px-4 rounded-md font-medium text-white ${
                  orderType === "buy"
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-red-600 hover:bg-red-700"
                } transition-colors`}
              >
                Place {orderType.toUpperCase()} Order
              </button>
            </form>
          </div>
        </div>

        {/* Order Book & Recent Orders */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Book */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">Order Book</h3>
            <div className="grid grid-cols-2 gap-4">
              {/* Buy Orders */}
              <div>
                <h4 className="text-sm font-medium text-green-600 mb-2">Buy Orders</h4>
                <div className="space-y-1">
                  {[
                    { price: 1024, quantity: 150 },
                    { price: 1023, quantity: 200 },
                    { price: 1022, quantity: 100 },
                  ].map((order, index) => (
                    <div key={index} className="flex justify-between text-sm bg-green-50 px-2 py-1 rounded">
                      <span>₹{order.price}</span>
                      <span>{order.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sell Orders */}
              <div>
                <h4 className="text-sm font-medium text-red-600 mb-2">Sell Orders</h4>
                <div className="space-y-1">
                  {[
                    { price: 1026, quantity: 120 },
                    { price: 1027, quantity: 180 },
                    { price: 1028, quantity: 90 },
                  ].map((order, index) => (
                    <div key={index} className="flex justify-between text-sm bg-red-50 px-2 py-1 rounded">
                      <span>₹{order.price}</span>
                      <span>{order.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* My Orders */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">My Orders</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-600 border-b">
                    <th className="pb-2">Type</th>
                    <th className="pb-2">Bond</th>
                    <th className="pb-2">Quantity</th>
                    <th className="pb-2">Price</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Time</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id} className="border-b">
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.type === "buy" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                        }`}>
                          {order.type.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2 text-sm">{order.bond}</td>
                      <td className="py-2 text-sm">{order.quantity}</td>
                      <td className="py-2 text-sm">₹{order.price}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.status === "filled" ? "bg-green-100 text-green-800" :
                          order.status === "open" ? "bg-blue-100 text-blue-800" :
                          order.status === "partial" ? "bg-yellow-100 text-yellow-800" :
                          "bg-gray-100 text-gray-800"
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="py-2 text-sm">
                        {new Date(order.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2">
                        {order.status === "open" && (
                          <button className="text-red-600 hover:text-red-800 text-sm">
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
