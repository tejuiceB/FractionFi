'use client';

import { useState, useEffect } from 'react';
import { apiService, type Bond, type Order, type Portfolio, type OrderCreate, type TradeHistoryItem } from './services/api';
import { useWallet } from './context/WalletContext';

// Utility function to format currency
const formatCurrency = (value: number | undefined): string => {
  return (value || 0).toFixed(2);
};

export default function Home() {
  const { account: walletAddress } = useWallet();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notifications, setNotifications] = useState<string[]>([]);
  const [selectedBond, setSelectedBond] = useState<Bond | null>(null);
  const [bonds, setBonds] = useState<Bond[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [tradeHistory, setTradeHistory] = useState<TradeHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Trading form states
  const [buyOrder, setBuyOrder] = useState({
    bond: '',
    quantity: '',
    price: ''
  });
  
  const [sellOrder, setSellOrder] = useState({
    bond: '',
    quantity: '',
    price: ''
  });

  // Utility function to format numbers
  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-IN', { 
      minimumFractionDigits: 0, 
      maximumFractionDigits: 2 
    });
  };

  // Initialize data on component mount
  useEffect(() => {
    const initialize = async () => {
      try {
        setLoading(true);
        console.log('Starting initialization...');
        
        // First, seed the database with sample data (only if needed)
        try {
          console.log('Testing API connection to: http://localhost:8000/api/v1');
          console.log('Seeding sample data...');
          const seedResult = await apiService.seedSampleData();
          console.log('Sample data result:', seedResult);
        } catch (seedError) {
          console.log('Seeding not needed or data already exists:', seedError);
          // This is not necessarily an error - data might already exist
        }
        
        // Load bonds
        console.log('Loading bonds...');
        const bondsData = await apiService.getBonds();
        console.log('Loaded bonds:', bondsData);
        console.log('Number of bonds loaded:', bondsData?.length || 0);
        
        if (bondsData && bondsData.length > 0) {
          setBonds(bondsData);
          setBuyOrder(prev => ({ ...prev, bond: `${bondsData[0].name} (${bondsData[0].coupon_rate}%)` }));
          setSellOrder(prev => ({ ...prev, bond: `${bondsData[0].name} (${bondsData[0].coupon_rate}%)` }));
        } else {
          console.warn('No bonds loaded from API, using fallback data');
          // Load demo bonds when API returns empty array
          const demoBonds = [
            {
              id: 'demo-1',
              name: 'HDFC Ltd 2024',
              isin: 'INE040A01034',
              coupon_rate: 8.5,
              maturity_date: '2024-12-31',
              face_value: 1000,
              min_unit: 1,
              status: 'active',
              current_price: 1050,
              total_volume_24h: 50000,
              price_change_24h: 25,
              price_change_percentage: 2.43,
              market_cap: 1000000,
              total_supply: 1000
            },
            {
              id: 'demo-2', 
              name: 'Tata Steel 2025',
              isin: 'INE081A01020',
              coupon_rate: 7.2,
              maturity_date: '2025-06-30',
              face_value: 1000,
              min_unit: 1,
              status: 'active',
              current_price: 980,
              total_volume_24h: 75000,
              price_change_24h: -15,
              price_change_percentage: -1.51,
              market_cap: 800000,
              total_supply: 800
            }
          ];
          setBonds(demoBonds);
          if (demoBonds.length > 0) {
            setBuyOrder(prev => ({ ...prev, bond: `${demoBonds[0].name} (${demoBonds[0].coupon_rate}%)` }));
            setSellOrder(prev => ({ ...prev, bond: `${demoBonds[0].name} (${demoBonds[0].coupon_rate}%)` }));
          }
          addNotification('⚠️ Backend returned no bonds. Using demo data.');
        }
        
        // Load portfolio and orders only if wallet is connected
        if (walletAddress && walletAddress.trim() !== '') {
          console.log('Loading user data for wallet:', walletAddress);
          await loadUserData(walletAddress);
        } else {
          console.log('No wallet connected, skipping user data load');
        }
        
      } catch (err) {
        console.error('Initialization error:', err);
        addNotification('❌ Failed to connect to backend. Please check if the backend server is running on port 8000.');
        
        // Add fallback demo data if API fails
        console.log('Adding fallback demo data...');
        const demoBonds = [
          {
            id: 'demo-1',
            name: 'HDFC Ltd 2024',
            isin: 'INE040A01034',
            coupon_rate: 8.5,
            maturity_date: '2024-12-31',
            face_value: 1000,
            min_unit: 1,
            status: 'active',
            current_price: 1050,
            total_volume_24h: 50000,
            price_change_24h: 25,
            price_change_percentage: 2.43,
            market_cap: 1000000,
            total_supply: 1000
          },
          {
            id: 'demo-2', 
            name: 'Tata Steel 2025',
            isin: 'INE081A01020',
            coupon_rate: 7.2,
            maturity_date: '2025-06-30',
            face_value: 1000,
            min_unit: 1,
            status: 'active',
            current_price: 980,
            total_volume_24h: 75000,
            price_change_24h: -15,
            price_change_percentage: -1.51,
            market_cap: 800000,
            total_supply: 800
          }
        ];
        setBonds(demoBonds);
        if (demoBonds.length > 0) {
          setBuyOrder(prev => ({ ...prev, bond: `${demoBonds[0].name} (${demoBonds[0].coupon_rate}%)` }));
          setSellOrder(prev => ({ ...prev, bond: `${demoBonds[0].name} (${demoBonds[0].coupon_rate}%)` }));
        }
        addNotification('🔄 Using demo data while backend is unavailable');
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, [walletAddress]); // Only re-run when wallet address changes

  // Separate useEffect to update order forms when bonds are loaded
  useEffect(() => {
    if (bonds.length > 0) {
      // Set default bond selection for order forms (but don't auto-open modal)
      setBuyOrder(prev => ({ 
        ...prev, 
        bond: prev.bond || `${bonds[0].name} (${bonds[0].coupon_rate}%)`,
        price: prev.price || (bonds[0].current_price || bonds[0].face_value).toString()
      }));
      setSellOrder(prev => ({ 
        ...prev, 
        bond: prev.bond || `${bonds[0].name} (${bonds[0].coupon_rate}%)`
      }));
    }
  }, [bonds]); // Only when bonds change

  const loadUserData = async (wallet: string) => {
    try {
      // Load portfolio (will auto-create user if doesn't exist)
      const portfolioData = await apiService.getPortfolio(wallet);
      setPortfolio(portfolioData);
      
      // Try to load orders, but don't fail if user doesn't have authentication yet
      try {
        const ordersData = await apiService.getOrders(wallet);
        setOrders(ordersData);
      } catch (orderErr) {
        console.log('Could not load orders (user may need to authenticate):', orderErr);
        setOrders([]); // Set empty orders array for new users
      }

      // Try to load trade history
      try {
        const tradesData = await apiService.getTradeHistory(wallet, 10); // Get last 10 trades
        setTradeHistory(tradesData);
      } catch (tradeErr) {
        console.log('Could not load trade history:', tradeErr);
        setTradeHistory([]); // Set empty trade history for new users
      }
      
    } catch (err) {
      console.error('Error loading user data:', err);
      // Don't set error here as user might not exist yet
    }
  };

  // Calculate total amounts
  const buyTotal = buyOrder.quantity && buyOrder.price ? 
    (parseFloat(buyOrder.quantity) * parseFloat(buyOrder.price)).toLocaleString() : '0';
    
  const sellTotal = sellOrder.quantity && sellOrder.price ? 
    (parseFloat(sellOrder.quantity) * parseFloat(sellOrder.price)).toLocaleString() : '0';

  // Add notification
  const addNotification = (message: string) => {
    setNotifications(prev => [...prev, message]);
    setTimeout(() => {
      setNotifications(prev => prev.slice(1));
    }, 3000);
  };

  // Handle form submissions with REAL API calls
  const handleBuyOrder = async () => {
    // Strict wallet requirement - no trading without wallet
    if (!walletAddress || walletAddress.trim() === '') {
      addNotification('❌ Wallet connection required! Please connect your MetaMask wallet to place orders.');
      return;
    }

    if (!buyOrder.quantity || !buyOrder.price || !buyOrder.bond) {
      addNotification('❌ Please fill in all fields (Bond, Quantity, and Price)');
      return;
    }

    // Find the selected bond from the bonds array
    const selectedBondForOrder = bonds.find(bond => `${bond.name} (${bond.coupon_rate}%)` === buyOrder.bond);
    if (!selectedBondForOrder) {
      addNotification('❌ Please select a valid bond');
      return;
    }

    try {
      const orderData: OrderCreate = {
        bond_id: selectedBondForOrder.id,
        side: 'buy',
        order_type: 'limit',
        price: parseFloat(buyOrder.price),
        quantity: parseFloat(buyOrder.quantity),
        user_wallet_address: walletAddress
      };

      await apiService.createOrder(orderData);
      addNotification(`✅ Buy order placed for ${buyOrder.quantity} units of ${selectedBondForOrder.name} at $${buyOrder.price} each`);
      
      // Refresh data to show new order and updated portfolio
      await loadUserData(walletAddress);
      
      // Clear form
      setBuyOrder({ ...buyOrder, quantity: '' });
      
    } catch (error) {
      console.error('Buy order error:', error);
      addNotification(`❌ Failed to place buy order: ${error}`);
    }
  };

  const handleSellOrder = async () => {
    // Strict wallet requirement - no trading without wallet
    if (!walletAddress || walletAddress.trim() === '') {
      addNotification('❌ Wallet connection required! Please connect your MetaMask wallet to place orders.');
      return;
    }

    if (!sellOrder.quantity || !sellOrder.price || !sellOrder.bond) {
      addNotification('❌ Please fill in all fields (Bond, Quantity, and Price)');
      return;
    }

    // Find the selected bond from the bonds array
    const selectedBondForOrder = bonds.find(bond => `${bond.name} (${bond.coupon_rate}%)` === sellOrder.bond);
    if (!selectedBondForOrder) {
      addNotification('❌ Please select a valid bond');
      return;
    }

    try {
      const orderData: OrderCreate = {
        bond_id: selectedBondForOrder.id,
        side: 'sell',
        order_type: 'limit',
        price: parseFloat(sellOrder.price),
        quantity: parseFloat(sellOrder.quantity),
        user_wallet_address: walletAddress
      };

      await apiService.createOrder(orderData);
      addNotification(`✅ Sell order placed for ${sellOrder.quantity} units of ${selectedBondForOrder.name} at $${sellOrder.price} each`);
      
      // Refresh data to show new order and updated portfolio
      await loadUserData(walletAddress);
      
      // Clear form
      setSellOrder({ ...sellOrder, quantity: '' });
      
    } catch (error) {
      console.error('Sell order error:', error);
      addNotification(`❌ Failed to place sell order: ${error}`);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    if (!walletAddress || walletAddress.trim() === '') {
      addNotification('❌ Wallet connection required to cancel orders.');
      return;
    }

    try {
      await apiService.cancelOrder(orderId);
      addNotification('✅ Order cancelled successfully');
      
      // Refresh data to show updated orders
      await loadUserData(walletAddress);
      
    } catch (error) {
      console.error('Cancel order error:', error);
      addNotification(`❌ Failed to cancel order: ${error}`);
    }
  };

  const showBondDetails = (bond: Bond) => {
    setSelectedBond(bond);
    addNotification(`📊 Viewing details for ${bond.name}`);
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Wallet Connection Prompt */}
      {(!walletAddress || walletAddress.trim() === '') && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <div className="text-blue-600">🔗</div>
            <div>
              <h3 className="text-lg font-medium text-blue-900">Connect Your Wallet</h3>
              <p className="text-blue-700">Connect your MetaMask wallet to view your portfolio and trade bonds.</p>
            </div>
          </div>
        </div>
      )}

      {/* Wallet Connected Info */}
      {walletAddress && walletAddress.trim() !== '' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="text-green-600">✅</div>
            <div>
              <h4 className="text-sm font-medium text-green-900">Wallet Connected</h4>
              <p className="text-green-700 text-xs font-mono">{walletAddress}</p>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-md">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-full">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Portfolio</p>
              <p className="text-2xl font-semibold text-gray-900">
                ${portfolio ? formatCurrency(portfolio.total_portfolio_value) : '0.00'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-md">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-full">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Bonds</p>
              <p className="text-2xl font-semibold text-gray-900">{portfolio ? portfolio.holdings_count : 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-md">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-full">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg. Yield</p>
              <p className="text-2xl font-semibold text-gray-900">7.8%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-md">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-full">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Monthly Yield</p>
              <p className="text-2xl font-semibold text-gray-900">₹1,890</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bond</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tradeHistory && tradeHistory.length > 0 ? (
                tradeHistory.map((trade, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{trade.bond_name}</div>
                        <div className="text-sm text-gray-500">{trade.isin}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        trade.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side.charAt(0).toUpperCase() + trade.side.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{formatNumber(trade.total_value)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Completed
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(trade.executed_at).toLocaleDateString('en-IN')}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    {tradeHistory ? 'No recent transactions' : 'Loading transactions...'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Open Orders */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Open Orders</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bond</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Side</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tx Hash</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders && orders.length > 0 ? (
                orders.map((order, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {bonds.find(b => b.id === order.bond_id)?.name || 'Unknown Bond'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {bonds.find(b => b.id === order.bond_id)?.isin || 'N/A'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        order.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {order.side.charAt(0).toUpperCase() + order.side.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatNumber(order.quantity)} 
                      {order.filled_quantity > 0 && (
                        <span className="text-gray-500"> ({formatNumber(order.filled_quantity)} filled)</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{formatNumber(order.price)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        order.status === 'open' ? 'bg-yellow-100 text-yellow-800' :
                        order.status === 'filled' ? 'bg-green-100 text-green-800' :
                        order.status === 'partially_filled' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1).replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.tx_hash ? (
                        <span className="font-mono text-xs text-blue-600" title={order.tx_hash}>
                          {order.tx_hash.slice(0, 10)}...{order.tx_hash.slice(-8)}
                        </span>
                      ) : (
                        <span className="text-gray-400">Pending</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleDateString('en-IN')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {order.status === 'open' && (
                        <button
                          onClick={() => handleCancelOrder(order.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-sm text-gray-500">
                    {orders ? 'No open orders' : 'Loading orders...'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderBondMarket = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Available Bonds</h3>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-center py-4">Loading bonds...</div>
          ) : bonds.length === 0 ? (
            <div className="text-center py-4 text-gray-500">No bonds available. Please check your connection.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {bonds.map((bond) => (
                <div key={bond.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                     onClick={() => showBondDetails(bond)}>
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-semibold text-gray-900">{bond.name}</h4>
                    <span className="text-green-600 font-bold">{bond.coupon_rate}%</span>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Current Price:</span>
                      <span className="font-medium">${formatCurrency(bond.current_price || bond.face_value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>24h Change:</span>
                      <span className={bond.price_change_percentage >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {(bond.price_change_percentage || 0) >= 0 ? '+' : ''}{formatCurrency(bond.price_change_percentage)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Min. Unit:</span>
                      <span>${bond.min_unit}</span>
                    </div>
                  </div>
                  <button 
                    onClick={() => {
                      setActiveTab('trading');
                      setBuyOrder({
                        ...buyOrder, 
                        bond: `${bond.name} (${bond.coupon_rate}%)`,
                        price: (bond.current_price || bond.face_value).toString()
                      });
                    }}
                    disabled={!walletAddress || walletAddress.trim() === ''}
                    className={`w-full mt-4 py-2 px-4 rounded-md transition-colors ${
                      !walletAddress || walletAddress.trim() === '' 
                        ? 'bg-gray-400 cursor-not-allowed text-gray-600'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {!walletAddress || walletAddress.trim() === '' ? 'Connect Wallet to Trade' : 'Trade Now'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderTrading = () => (
    <div className="space-y-6">
      {/* Wallet Connection Prompt */}
      {(!walletAddress || walletAddress.trim() === '') && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <div className="text-orange-600">⚠️</div>
            <div>
              <h3 className="text-lg font-medium text-orange-900">Wallet Required for Trading</h3>
              <p className="text-orange-700">Please connect your MetaMask wallet to place buy and sell orders.</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Buy Order */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-green-700">Place Buy Order</h3>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Bond</label>
            <select 
              value={buyOrder.bond}
              onChange={(e) => setBuyOrder({...buyOrder, bond: e.target.value})}
              disabled={!walletAddress || walletAddress.trim() === ''}
              className={`w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                !walletAddress || walletAddress.trim() === '' ? 'bg-gray-100 cursor-not-allowed' : ''
              }`}
            >
              <option value="">-- {!walletAddress ? 'Connect wallet first' : 'Select a Bond'} --</option>
              {bonds.map((bond) => (
                <option key={bond.id} value={`${bond.name} (${bond.coupon_rate}%)`}>
                  {bond.name} ({bond.coupon_rate}%) - ${bond.current_price || bond.face_value}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
            <input 
              type="number" 
              placeholder={!walletAddress ? "Connect wallet first" : "Enter quantity"}
              value={buyOrder.quantity}
              onChange={(e) => setBuyOrder({...buyOrder, quantity: e.target.value})}
              disabled={!walletAddress || walletAddress.trim() === ''}
              className={`w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                !walletAddress || walletAddress.trim() === '' ? 'bg-gray-100 cursor-not-allowed' : ''
              }`}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Price per Unit</label>
            <input 
              type="number" 
              placeholder={!walletAddress ? "Connect wallet first" : "₹1,050"}
              value={buyOrder.price}
              onChange={(e) => setBuyOrder({...buyOrder, price: e.target.value})}
              disabled={!walletAddress || walletAddress.trim() === ''}
              className={`w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                !walletAddress || walletAddress.trim() === '' ? 'bg-gray-100 cursor-not-allowed' : ''
              }`}
            />
          </div>
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="flex justify-between text-sm">
              <span>Total Amount:</span>
              <span className="font-semibold">₹{buyTotal}</span>
            </div>
          </div>
          <button 
            onClick={handleBuyOrder}
            disabled={!walletAddress || walletAddress.trim() === ''}
            className={`w-full py-2 px-4 rounded-md transition-colors ${
              !walletAddress || walletAddress.trim() === ''
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {!walletAddress || walletAddress.trim() === '' 
              ? 'Connect Wallet to Buy' 
              : 'Place Buy Order'
            }
          </button>
        </div>
      </div>

      {/* Sell Order */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-red-700">Place Sell Order</h3>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Bond from Portfolio</label>
            <select 
              value={sellOrder.bond}
              onChange={(e) => setSellOrder({...sellOrder, bond: e.target.value})}
              disabled={!walletAddress || walletAddress.trim() === ''}
              className={`w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                !walletAddress || walletAddress.trim() === '' ? 'bg-gray-100 cursor-not-allowed' : ''
              }`}
            >
              <option value="">-- {!walletAddress ? 'Connect wallet first' : 'Select a Bond from Portfolio'} --</option>
              {portfolio && portfolio.holdings.length > 0 ? (
                portfolio.holdings.map((holding, index) => (
                  <option key={index} value={`${holding.bond_name}`}>
                    {holding.bond_name} ({formatNumber(holding.quantity)} units)
                  </option>
                ))
              ) : (
                <option value="" disabled>No holdings available</option>
              )}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity to Sell</label>
            <input 
              type="number" 
              placeholder={!walletAddress ? "Connect wallet first" : "Enter quantity"}
              value={sellOrder.quantity}
              onChange={(e) => setSellOrder({...sellOrder, quantity: e.target.value})}
              disabled={!walletAddress || walletAddress.trim() === ''}
              className={`w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                !walletAddress || walletAddress.trim() === '' ? 'bg-gray-100 cursor-not-allowed' : ''
              }`}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Selling Price per Unit</label>
            <input 
              type="number" 
              placeholder={!walletAddress ? "Connect wallet first" : "₹1,080"}
              value={sellOrder.price}
              onChange={(e) => setSellOrder({...sellOrder, price: e.target.value})}
              disabled={!walletAddress || walletAddress.trim() === ''}
              className={`w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                !walletAddress || walletAddress.trim() === '' ? 'bg-gray-100 cursor-not-allowed' : ''
              }`}
            />
          </div>
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="flex justify-between text-sm">
              <span>Total Amount:</span>
              <span className="font-semibold">₹{sellTotal}</span>
            </div>
          </div>
          <button 
            onClick={handleSellOrder}
            disabled={!walletAddress || walletAddress.trim() === ''}
            className={`w-full py-2 px-4 rounded-md transition-colors ${
              !walletAddress || walletAddress.trim() === ''
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-red-600 text-white hover:bg-red-700'
            }`}
          >
            {!walletAddress || walletAddress.trim() === '' 
              ? 'Connect Wallet to Sell' 
              : 'Place Sell Order'
            }
          </button>
        </div>
      </div>
      </div>
    </div>
  );

  const renderPortfolio = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">My Bond Portfolio</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bond</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purchase Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Maturity</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {portfolio && portfolio.holdings.length > 0 ? (
                portfolio.holdings.map((holding, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{holding.bond_name}</div>
                        <div className="text-sm text-gray-500">{holding.isin}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatNumber(holding.quantity)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{formatNumber(holding.current_price)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{formatNumber(holding.market_value)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ₹{formatNumber(holding.unrealized_pnl)} ({formatNumber(holding.pnl_percentage)}%)
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {/* Maturity date would come from bond details */}
                      -
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                    {portfolio ? 'No holdings found' : 'Loading portfolio...'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2">
          {notifications.map((notification, index) => (
            <div
              key={index}
              className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm animate-slide-in"
            >
              <p className="text-sm">{notification}</p>
            </div>
          ))}
        </div>
      )}

      {/* Bond Details Modal */}
      {selectedBond && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-900">{selectedBond.name} Bond Details</h3>
              <button
                onClick={() => setSelectedBond(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">ISIN:</span>
                <span className="font-semibold">{selectedBond.isin}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Coupon Rate:</span>
                <span className="font-semibold text-green-600">{selectedBond.coupon_rate}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Current Price:</span>
                <span className="font-semibold">${formatCurrency(selectedBond.current_price || selectedBond.face_value)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Face Value:</span>
                <span className="font-semibold">${formatCurrency(selectedBond.face_value)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">24h Volume:</span>
                <span className="font-semibold">${formatCurrency(selectedBond.total_volume_24h)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Min. Unit:</span>
                <span className="font-semibold">${formatCurrency(selectedBond.min_unit)}</span>
              </div>
            </div>
            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => {
                  setActiveTab('trading');
                  setBuyOrder({
                    ...buyOrder,
                    bond: `${selectedBond.name} (${selectedBond.coupon_rate}%)`,
                    price: (selectedBond.current_price || selectedBond.face_value).toString()
                  });
                  setSelectedBond(null);
                }}
                disabled={!walletAddress || walletAddress.trim() === ''}
                className={`flex-1 py-2 px-4 rounded-md transition-colors ${
                  !walletAddress || walletAddress.trim() === '' 
                    ? 'bg-gray-400 cursor-not-allowed text-gray-600'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {!walletAddress || walletAddress.trim() === '' ? 'Connect Wallet to Trade' : 'Trade Now'}
              </button>
              <button
                onClick={() => setSelectedBond(null)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mb-8">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: '📊' },
            { id: 'market', label: 'Bond Market', icon: '📈' },
            { id: 'trading', label: 'Trading', icon: '💹' },
            { id: 'portfolio', label: 'Portfolio', icon: '💼' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700 border-b-2 border-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'market' && renderBondMarket()}
      {activeTab === 'trading' && renderTrading()}
      {activeTab === 'portfolio' && renderPortfolio()}
    </div>
  );
}
