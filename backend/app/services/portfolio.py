from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from decimal import Decimal
from datetime import datetime, timedelta

from app.models.models import User, Bond, Holding, Trade, Order


class PortfolioService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def update_holdings_from_trade(self, trade: Trade) -> None:
        """Update user holdings after a trade execution"""
        
        # Get buy and sell orders
        buy_order = self.db.query(Order).filter(Order.id == trade.buy_order_id).first()
        sell_order = self.db.query(Order).filter(Order.id == trade.sell_order_id).first()
        
        if not buy_order or not sell_order:
            return
        
        # Update buyer's holdings (increase)
        buyer_holding = self.db.query(Holding).filter(
            and_(
                Holding.user_id == buy_order.user_id,
                Holding.bond_id == trade.bond_id
            )
        ).first()
        
        if buyer_holding:
            buyer_holding.quantity += trade.quantity
        else:
            buyer_holding = Holding(
                user_id=buy_order.user_id,
                bond_id=trade.bond_id,
                quantity=trade.quantity
            )
            self.db.add(buyer_holding)
        
        # Update seller's holdings (decrease)
        seller_holding = self.db.query(Holding).filter(
            and_(
                Holding.user_id == sell_order.user_id,
                Holding.bond_id == trade.bond_id
            )
        ).first()
        
        if seller_holding:
            seller_holding.quantity -= trade.quantity
            # Remove holding if quantity becomes 0
            if seller_holding.quantity <= 0:
                self.db.delete(seller_holding)
    
    def get_user_portfolio(self, wallet_address: str) -> Dict:
        """Get complete portfolio for a user"""
        
        user = self.db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return {"error": "User not found"}
        
        # Get all holdings with bond details
        holdings_query = self.db.query(Holding, Bond).join(
            Bond, Holding.bond_id == Bond.id
        ).filter(Holding.user_id == user.id).all()
        
        portfolio = []
        total_portfolio_value = Decimal('0')
        
        for holding, bond in holdings_query:
            # Get current market price (last trade price)
            last_trade = self.db.query(Trade).filter(
                Trade.bond_id == bond.id
            ).order_by(desc(Trade.executed_at)).first()
            
            current_price = last_trade.price if last_trade else bond.face_value
            market_value = holding.quantity * current_price
            total_portfolio_value += market_value
            
            # Calculate PnL (simplified - would need cost basis in real system)
            cost_basis = holding.quantity * bond.face_value  # Simplified
            unrealized_pnl = market_value - cost_basis
            pnl_percentage = float((unrealized_pnl / cost_basis) * 100) if cost_basis > 0 else 0.0
            
            portfolio.append({
                "bond_id": str(bond.id),
                "bond_name": bond.name,
                "isin": bond.isin,
                "quantity": float(holding.quantity),
                "current_price": float(current_price),
                "market_value": float(market_value),
                "unrealized_pnl": float(unrealized_pnl),
                "pnl_percentage": pnl_percentage,
                "coupon_rate": bond.coupon_rate,
                "maturity_date": bond.maturity_date.isoformat()
            })
        
        return {
            "user_id": str(user.id),
            "wallet_address": user.wallet_address,
            "total_portfolio_value": float(total_portfolio_value),
            "holdings": portfolio,
            "holdings_count": len(portfolio)
        }
    
    def get_user_trade_history(self, wallet_address: str, limit: int = 100) -> List[Dict]:
        """Get trade history for a user"""
        
        user = self.db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return []
        
        # Get all user orders
        user_orders = self.db.query(Order.id).filter(Order.user_id == user.id).subquery()
        
        # Get trades where user was buyer or seller
        trades = self.db.query(Trade, Bond).join(
            Bond, Trade.bond_id == Bond.id
        ).filter(
            or_(
                Trade.buy_order_id.in_(user_orders),
                Trade.sell_order_id.in_(user_orders)
            )
        ).order_by(desc(Trade.executed_at)).limit(limit).all()
        
        trade_history = []
        
        for trade, bond in trades:
            # Determine if user was buyer or seller
            buy_order = self.db.query(Order).filter(Order.id == trade.buy_order_id).first()
            sell_order = self.db.query(Order).filter(Order.id == trade.sell_order_id).first()
            
            user_side = "buy" if buy_order.user_id == user.id else "sell"
            
            trade_history.append({
                "trade_id": str(trade.id),
                "bond_name": bond.name,
                "isin": bond.isin,
                "side": user_side,
                "price": float(trade.price),
                "quantity": float(trade.quantity),
                "total_value": float(trade.price * trade.quantity),
                "executed_at": trade.executed_at.isoformat(),
                "tx_hash": trade.tx_hash
            })
        
        return trade_history
    
    def get_portfolio_performance(self, wallet_address: str, days: int = 30) -> Dict:
        """Get portfolio performance metrics"""
        
        user = self.db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return {"error": "User not found"}
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user orders in time period
        user_orders = self.db.query(Order.id).filter(
            and_(
                Order.user_id == user.id,
                Order.created_at >= start_date
            )
        ).subquery()
        
        # Calculate trading volume
        trading_volume = self.db.query(
            func.sum(Trade.price * Trade.quantity)
        ).filter(
            and_(
                or_(
                    Trade.buy_order_id.in_(user_orders),
                    Trade.sell_order_id.in_(user_orders)
                ),
                Trade.executed_at >= start_date
            )
        ).scalar() or Decimal('0')
        
        # Count trades
        trade_count = self.db.query(Trade).filter(
            and_(
                or_(
                    Trade.buy_order_id.in_(user_orders),
                    Trade.sell_order_id.in_(user_orders)
                ),
                Trade.executed_at >= start_date
            )
        ).count()
        
        current_portfolio = self.get_user_portfolio(wallet_address)
        
        return {
            "period_days": days,
            "trading_volume": float(trading_volume),
            "trade_count": trade_count,
            "current_portfolio_value": current_portfolio.get("total_portfolio_value", 0),
            "holdings_count": current_portfolio.get("holdings_count", 0)
        }
