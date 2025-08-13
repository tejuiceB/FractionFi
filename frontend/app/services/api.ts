// API Configuration and Service
const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface Bond {
  id: string;
  name: string;
  isin: string;
  coupon_rate: number;
  maturity_date: string;
  face_value: number;
  min_unit: number;
  status: string;
  current_price?: number;
  total_volume_24h: number;
  price_change_24h: number;
  price_change_percentage: number;
  market_cap: number;
  total_supply?: number;
}

export interface Order {
  id: string;
  bond_id: string;
  side: 'buy' | 'sell';
  order_type: 'limit' | 'market';
  price: number;
  quantity: number;
  filled_quantity: number;
  status: string;
  tx_hash?: string;
  created_at: string;
  updated_at?: string;
}

export interface OrderCreate {
  bond_id: string;
  side: 'buy' | 'sell';
  order_type: 'limit' | 'market';
  price: number;
  quantity: number;
  user_wallet_address: string;
}

export interface Portfolio {
  user_id: string;
  wallet_address: string;
  total_portfolio_value: number;
  holdings: PortfolioHolding[];
  holdings_count: number;
}

export interface PortfolioHolding {
  bond_id: string;
  bond_name: string;
  isin: string;
  quantity: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  pnl_percentage: number;
  coupon_rate: number;
  maturity_date: string;
}

export interface TradeHistoryItem {
  trade_id: string;
  bond_name: string;
  isin: string;
  side: string;
  price: number;
  quantity: number;
  total_value: number;
  executed_at: string;
  tx_hash?: string;
}

class ApiService {
  private async fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      console.log(`Making API request to: ${API_BASE_URL}${endpoint}`);
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      console.log(`API response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`API request failed: ${response.statusText}`, errorText);
        throw new Error(`API request failed: ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log(`API response data:`, data);
      return data;
    } catch (error) {
      console.error(`Fetch error for ${endpoint}:`, error);
      throw error;
    }
  }

  // Bond APIs
  async getBonds(): Promise<Bond[]> {
    return this.fetchApi<Bond[]>('/bonds/');
  }

  async getBond(bondId: string): Promise<Bond> {
    return this.fetchApi<Bond>(`/bonds/${bondId}`);
  }

  async getBondOrderBook(bondId: string) {
    return this.fetchApi(`/orders/${bondId}/orderbook`);
  }

  async getBondStats(bondId: string) {
    return this.fetchApi(`/bonds/${bondId}/stats`);
  }

  // Order APIs
  async createOrder(orderData: OrderCreate): Promise<Order> {
    // Use public endpoint for wallet-based order creation
    return this.fetchApi<Order>('/orders/public/create', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  }

  async getOrders(walletAddress?: string): Promise<Order[]> {
    if (walletAddress) {
      // Use public endpoint for wallet-based queries
      return this.fetchApi<Order[]>(`/orders/public/by-wallet?wallet_address=${walletAddress}`);
    } else {
      // Use authenticated endpoint for general queries (requires auth)
      return this.fetchApi<Order[]>(`/orders/`);
    }
  }

  async cancelOrder(orderId: string): Promise<{ message: string }> {
    return this.fetchApi(`/orders/${orderId}`, {
      method: 'DELETE',
    });
  }

  async getTrades(bondId?: string, walletAddress?: string) {
    const params = new URLSearchParams();
    if (bondId) params.append('bond_id', bondId);
    if (walletAddress) params.append('wallet_address', walletAddress);
    
    return this.fetchApi(`/orders/trades/?${params.toString()}`);
  }

  // Portfolio APIs
  async getPortfolio(walletAddress: string): Promise<Portfolio> {
    return this.fetchApi<Portfolio>(`/portfolio/${walletAddress}`);
  }

  async getTradeHistory(walletAddress: string, limit: number = 100): Promise<TradeHistoryItem[]> {
    return this.fetchApi<TradeHistoryItem[]>(`/portfolio/${walletAddress}/trades?limit=${limit}`);
  }

  async getPerformance(walletAddress: string, days: number = 30) {
    return this.fetchApi(`/portfolio/${walletAddress}/performance?days=${days}`);
  }

  // Admin APIs (for testing)
  async seedSampleData() {
    return this.fetchApi('/admin/seed-data', {
      method: 'POST',
    });
  }

  async clearData() {
    return this.fetchApi('/admin/clear-data', {
      method: 'DELETE',
    });
  }
}

export const apiService = new ApiService();
