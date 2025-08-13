from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from decimal import Decimal
import uuid
from datetime import datetime

from app.models.models import Order, Trade, Bond


class OrderMatchingEngine:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def match_order(self, order_id: str) -> List[Trade]:
        """
        Match an order against existing orders in the order book.
        Returns list of executed trades.
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != "open":
            return []
        
        trades = []
        remaining_quantity = order.quantity - order.filled_quantity
        
        if order.side == "buy":
            trades = self._match_buy_order(order, remaining_quantity)
        else:
            trades = self._match_sell_order(order, remaining_quantity)
        
        # Update order status based on fill
        if order.filled_quantity >= order.quantity:
            order.status = "filled"
        elif order.filled_quantity > 0:
            order.status = "partial"
        
        self.db.commit()
        return trades
    
    def _match_buy_order(self, buy_order: Order, remaining_quantity: Decimal) -> List[Trade]:
        """Match a buy order against sell orders"""
        trades = []
        
        # Find matching sell orders (price <= buy_order.price)
        matching_sells = self.db.query(Order).filter(
            and_(
                Order.bond_id == buy_order.bond_id,
                Order.side == "sell",
                Order.status == "open",
                Order.price <= buy_order.price,
                Order.id != buy_order.id
            )
        ).order_by(asc(Order.price), asc(Order.created_at)).all()
        
        for sell_order in matching_sells:
            if remaining_quantity <= 0:
                break
            
            # Calculate trade quantity
            sell_available = sell_order.quantity - sell_order.filled_quantity
            trade_quantity = min(remaining_quantity, sell_available)
            
            if trade_quantity > 0:
                # Execute trade at sell order price (maker price)
                trade = Trade(
                    id=uuid.uuid4(),
                    buy_order_id=buy_order.id,
                    sell_order_id=sell_order.id,
                    bond_id=buy_order.bond_id,
                    price=sell_order.price,
                    quantity=trade_quantity,
                    executed_at=datetime.utcnow()
                )
                
                # Update order fill quantities
                buy_order.filled_quantity += trade_quantity
                sell_order.filled_quantity += trade_quantity
                
                # Update sell order status
                if sell_order.filled_quantity >= sell_order.quantity:
                    sell_order.status = "filled"
                elif sell_order.filled_quantity > 0:
                    sell_order.status = "partial"
                
                self.db.add(trade)
                trades.append(trade)
                remaining_quantity -= trade_quantity
        
        return trades
    
    def _match_sell_order(self, sell_order: Order, remaining_quantity: Decimal) -> List[Trade]:
        """Match a sell order against buy orders"""
        trades = []
        
        # Find matching buy orders (price >= sell_order.price)
        matching_buys = self.db.query(Order).filter(
            and_(
                Order.bond_id == sell_order.bond_id,
                Order.side == "buy",
                Order.status == "open",
                Order.price >= sell_order.price,
                Order.id != sell_order.id
            )
        ).order_by(desc(Order.price), asc(Order.created_at)).all()
        
        for buy_order in matching_buys:
            if remaining_quantity <= 0:
                break
            
            # Calculate trade quantity
            buy_available = buy_order.quantity - buy_order.filled_quantity
            trade_quantity = min(remaining_quantity, buy_available)
            
            if trade_quantity > 0:
                # Execute trade at buy order price (maker price)
                trade = Trade(
                    id=uuid.uuid4(),
                    buy_order_id=buy_order.id,
                    sell_order_id=sell_order.id,
                    bond_id=sell_order.bond_id,
                    price=buy_order.price,
                    quantity=trade_quantity,
                    executed_at=datetime.utcnow()
                )
                
                # Update order fill quantities
                buy_order.filled_quantity += trade_quantity
                sell_order.filled_quantity += trade_quantity
                
                # Update buy order status
                if buy_order.filled_quantity >= buy_order.quantity:
                    buy_order.status = "filled"
                elif buy_order.filled_quantity > 0:
                    buy_order.status = "partial"
                
                self.db.add(trade)
                trades.append(trade)
                remaining_quantity -= trade_quantity
        
        return trades
    
    def get_order_book(self, bond_id: str, depth: int = 10) -> dict:
        """Get current order book for a bond"""
        
        # Get buy orders (bids)
        bids = self.db.query(Order).filter(
            and_(
                Order.bond_id == bond_id,
                Order.side == "buy",
                Order.status == "open"
            )
        ).order_by(desc(Order.price), asc(Order.created_at)).limit(depth).all()
        
        # Get sell orders (asks)  
        asks = self.db.query(Order).filter(
            and_(
                Order.bond_id == bond_id,
                Order.side == "sell", 
                Order.status == "open"
            )
        ).order_by(asc(Order.price), asc(Order.created_at)).limit(depth).all()
        
        return {
            "bids": [
                {
                    "price": float(order.price),
                    "quantity": float(order.quantity - order.filled_quantity),
                    "order_id": str(order.id)
                }
                for order in bids
            ],
            "asks": [
                {
                    "price": float(order.price),
                    "quantity": float(order.quantity - order.filled_quantity),
                    "order_id": str(order.id)
                }
                for order in asks
            ]
        }
