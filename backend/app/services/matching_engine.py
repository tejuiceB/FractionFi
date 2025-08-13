import uuid
from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.models import Order, Trade, Holding, User, Bond
from app.core.websocket import ConnectionManager
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, db: Session, ws_manager: ConnectionManager):
        self.db = db
        self.ws_manager = ws_manager
    
    def process_order(self, order: Order) -> List[Trade]:
        """
        Process an order through the matching engine
        Returns list of trades created
        """
        trades = []
        
        if order.side == "buy":
            trades = self._match_buy_order(order)
        else:
            trades = self._match_sell_order(order)
        
        # Update order status
        self._update_order_status(order)
        
        # Broadcast updates via WebSocket
        self._broadcast_updates(order, trades)
        
        return trades
    
    def _match_buy_order(self, buy_order: Order) -> List[Trade]:
        """Match a buy order with existing sell orders"""
        trades = []
        
        # Find matching sell orders (price <= buy_order.price)
        # Ordered by price (ascending) then created_at (ascending) for price-time priority
        matching_orders = self.db.query(Order).filter(
            and_(
                Order.bond_id == buy_order.bond_id,
                Order.side == "sell",
                Order.status.in_(["open", "partial"]),
                Order.price <= buy_order.price,
                Order.user_id != buy_order.user_id  # Can't trade with yourself
            )
        ).order_by(Order.price.asc(), Order.created_at.asc()).all()
        
        remaining_quantity = buy_order.quantity - buy_order.filled_quantity
        
        for sell_order in matching_orders:
            if remaining_quantity <= 0:
                break
            
            available_quantity = sell_order.quantity - sell_order.filled_quantity
            if available_quantity <= 0:
                continue
            
            # Determine trade quantity
            trade_quantity = min(remaining_quantity, available_quantity)
            trade_price = sell_order.price  # Taker pays maker's price
            
            # Create trade
            trade = self._create_trade(buy_order, sell_order, trade_quantity, trade_price)
            trades.append(trade)
            
            # Update order filled quantities
            buy_order.filled_quantity += trade_quantity
            sell_order.filled_quantity += trade_quantity
            
            # Update holdings
            self._update_holdings(buy_order.user_id, sell_order.user_id, 
                                buy_order.bond_id, trade_quantity)
            
            remaining_quantity -= trade_quantity
            
            # Update sell order status
            self._update_order_status(sell_order)
        
        return trades
    
    def _match_sell_order(self, sell_order: Order) -> List[Trade]:
        """Match a sell order with existing buy orders"""
        trades = []
        
        # Find matching buy orders (price >= sell_order.price)
        # Ordered by price (descending) then created_at (ascending) for price-time priority
        matching_orders = self.db.query(Order).filter(
            and_(
                Order.bond_id == sell_order.bond_id,
                Order.side == "buy",
                Order.status.in_(["open", "partial"]),
                Order.price >= sell_order.price,
                Order.user_id != sell_order.user_id  # Can't trade with yourself
            )
        ).order_by(Order.price.desc(), Order.created_at.asc()).all()
        
        remaining_quantity = sell_order.quantity - sell_order.filled_quantity
        
        for buy_order in matching_orders:
            if remaining_quantity <= 0:
                break
            
            available_quantity = buy_order.quantity - buy_order.filled_quantity
            if available_quantity <= 0:
                continue
            
            # Determine trade quantity
            trade_quantity = min(remaining_quantity, available_quantity)
            trade_price = buy_order.price  # Taker gets maker's price
            
            # Create trade
            trade = self._create_trade(buy_order, sell_order, trade_quantity, trade_price)
            trades.append(trade)
            
            # Update order filled quantities
            buy_order.filled_quantity += trade_quantity
            sell_order.filled_quantity += trade_quantity
            
            # Update holdings
            self._update_holdings(buy_order.user_id, sell_order.user_id,
                                sell_order.bond_id, trade_quantity)
            
            remaining_quantity -= trade_quantity
            
            # Update buy order status
            self._update_order_status(buy_order)
        
        return trades
    
    def _create_trade(self, buy_order: Order, sell_order: Order, 
                     quantity: Decimal, price: Decimal) -> Trade:
        """Create a trade record"""
        from app.api.api_v1.endpoints.orders import generate_mock_tx_hash
        
        trade = Trade(
            id=uuid.uuid4(),
            buy_order_id=buy_order.id,
            sell_order_id=sell_order.id,
            bond_id=buy_order.bond_id,
            price=price,
            quantity=quantity,
            executed_at=datetime.utcnow(),
            tx_hash=generate_mock_tx_hash()  # Add transaction hash
        )
        
        self.db.add(trade)
        self.db.commit()
        
        logger.info(f"Trade created: {trade.id} - {quantity} @ {price} - TX: {trade.tx_hash}")
        
        return trade
    
    def _update_holdings(self, buyer_id: uuid.UUID, seller_id: uuid.UUID, 
                        bond_id: uuid.UUID, quantity: Decimal):
        """Update user holdings after a trade"""
        
        # Update buyer's holdings (increase)
        buyer_holding = self.db.query(Holding).filter(
            and_(Holding.user_id == buyer_id, Holding.bond_id == bond_id)
        ).first()
        
        if buyer_holding:
            buyer_holding.quantity += quantity
        else:
            buyer_holding = Holding(
                user_id=buyer_id,
                bond_id=bond_id,
                quantity=quantity
            )
            self.db.add(buyer_holding)
        
        # Update seller's holdings (decrease)
        seller_holding = self.db.query(Holding).filter(
            and_(Holding.user_id == seller_id, Holding.bond_id == bond_id)
        ).first()
        
        if seller_holding:
            seller_holding.quantity -= quantity
            # Remove holding if quantity becomes zero
            if seller_holding.quantity <= 0:
                self.db.delete(seller_holding)
        
        self.db.commit()
    
    def _update_order_status(self, order: Order):
        """Update order status based on filled quantity"""
        if order.filled_quantity >= order.quantity:
            order.status = "filled"
        elif order.filled_quantity > 0:
            order.status = "partial"
        
        self.db.commit()
    
    def _broadcast_updates(self, order: Order, trades: List[Trade]):
        """Broadcast updates via WebSocket"""
        try:
            # Run async broadcast in event loop
            asyncio.create_task(self._async_broadcast_updates(order, trades))
        except Exception as e:
            logger.error(f"Error broadcasting updates: {e}")
    
    async def _async_broadcast_updates(self, order: Order, trades: List[Trade]):
        """Async implementation of broadcast updates"""
        try:
            # Broadcast orderbook update
            orderbook = self.get_orderbook(order.bond_id)
            await self.ws_manager.broadcast_to_room(f"bond_{order.bond_id}", {
                "type": "orderbook_update",
                "data": orderbook
            })
            
            # Broadcast trade updates
            for trade in trades:
                await self.ws_manager.broadcast_to_room(f"bond_{order.bond_id}", {
                    "type": "trade",
                    "data": {
                        "id": str(trade.id),
                        "price": float(trade.price),
                        "quantity": float(trade.quantity),
                        "executed_at": trade.executed_at.isoformat()
                    }
                })
            
            # Broadcast portfolio updates to affected users
            affected_users = set()
            if trades:
                for trade in trades:
                    buy_order = self.db.query(Order).filter(Order.id == trade.buy_order_id).first()
                    sell_order = self.db.query(Order).filter(Order.id == trade.sell_order_id).first()
                    if buy_order and sell_order:
                        affected_users.add(buy_order.user_id)
                        affected_users.add(sell_order.user_id)
                
                for user_id in affected_users:
                    await self.ws_manager.broadcast_to_user(str(user_id), {
                        "type": "portfolio_update",
                        "message": "Your portfolio has been updated"
                    })
        
        except Exception as e:
            logger.error(f"Error in async broadcast updates: {e}")
    
    def get_orderbook(self, bond_id: uuid.UUID) -> dict:
        """Get current orderbook for a bond"""
        
        # Get buy orders (bids) - highest price first
        buy_orders = self.db.query(Order).filter(
            and_(
                Order.bond_id == bond_id,
                Order.side == "buy",
                Order.status.in_(["open", "partial"])
            )
        ).order_by(Order.price.desc()).limit(10).all()
        
        # Get sell orders (asks) - lowest price first
        sell_orders = self.db.query(Order).filter(
            and_(
                Order.bond_id == bond_id,
                Order.side == "sell",
                Order.status.in_(["open", "partial"])
            )
        ).order_by(Order.price.asc()).limit(10).all()
        
        bids = [
            {
                "price": float(order.price),
                "quantity": float(order.quantity - order.filled_quantity),
                "total": float(order.price * (order.quantity - order.filled_quantity))
            }
            for order in buy_orders
        ]
        
        asks = [
            {
                "price": float(order.price),
                "quantity": float(order.quantity - order.filled_quantity),
                "total": float(order.price * (order.quantity - order.filled_quantity))
            }
            for order in sell_orders
        ]
        
        return {
            "bids": bids,
            "asks": asks,
            "bond_id": str(bond_id)
        }
    
    def cancel_order(self, order_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Cancel an order"""
        order = self.db.query(Order).filter(
            and_(Order.id == order_id, Order.user_id == user_id)
        ).first()
        
        if not order or order.status not in ["open", "partial"]:
            return False
        
        order.status = "cancelled"
        self.db.commit()
        
        # Broadcast orderbook update
        self._broadcast_updates(order, [])
        
        return True
