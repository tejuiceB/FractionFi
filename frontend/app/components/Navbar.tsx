"use client";

import { useWallet } from "../context/WalletContext";
import { useState, useEffect } from "react";

export function Navbar() {
  const { isConnected, account, isMetaMaskInstalled, connectWallet, disconnectWallet, loading } = useWallet();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🏦</div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">FractionFi</h1>
              <p className="text-xs text-gray-500">Tokenized Bond Platform</p>
            </div>
          </div>

          {/* Status Indicators */}
          <div className="flex items-center space-x-4">
            {/* MetaMask Debug Info (temporary for debugging) */}
            {mounted && process.env.NODE_ENV === 'development' && (
              <div className="text-xs text-gray-500">
                {window.ethereum ? 
                  `ETH: ${window.ethereum.isMetaMask ? 'MM' : 'Other'}` : 'No ETH'}
              </div>
            )}
            
            {/* Network Status */}
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">Local Network</span>
            </div>

            {/* Wallet Connection */}
            {!loading ? (
              isConnected ? (
                <div className="flex items-center space-x-3">
                  <div className="text-sm text-gray-600">
                    <div className="font-medium">Connected</div>
                    <div className="text-xs">{account.slice(0, 6)}...{account.slice(-4)}</div>
                  </div>
                  <button
                    onClick={disconnectWallet}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                  >
                    Disconnect
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  {!isMetaMaskInstalled && (
                    <div className="text-xs text-red-600">
                      MetaMask not detected
                    </div>
                  )}
                  <button
                    onClick={connectWallet}
                    className={`px-4 py-2 text-white rounded-md transition-colors ${
                      isMetaMaskInstalled 
                        ? 'bg-blue-600 hover:bg-blue-700' 
                        : 'bg-gray-500 hover:bg-gray-600'
                    }`}
                  >
                    {isMetaMaskInstalled ? 'Connect Wallet' : 'Install MetaMask'}
                  </button>
                </div>
              )
            ) : (
              // Loading state during hydration
              <div className="px-4 py-2 bg-gray-200 text-gray-500 rounded-md">
                Loading...
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
