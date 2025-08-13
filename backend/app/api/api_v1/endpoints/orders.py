from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
import uuid
import secrets

from app.db.database import get_db
from app.models.models import Order, Bond, User, Trade, Holding
from app.services.matching_engine import MatchingEngine
from app.core.websocket import manager
from app.core.auth import get_current_active_user, require_kyc_verified

router = APIRouter()

def generate_mock_tx_hash() -> str:
    """Generate a realistic-looking blockchain transaction hash"""
    return "0x" + secrets.token_hex(32)

def create_demo_holdings_for_new_user(db: Session, user: User):
    """Create demo holdings for a new user to enable trading"""
    try:
        # Check if user already has holdings
        existing_holdings = db.query(Holding).filter(Holding.user_id == user.id).first()
        if existing_holdings:
            return True  # User already has holdings
        
        # Get first 2 available bonds
        available_bonds = db.query(Bond).filter(Bond.status == "active").limit(2).all()
        
        if available_bonds:
            for i, bond in enumerate(available_bonds):
                # Give new users some demo holdings to start trading
                demo_quantity = Decimal('10') if i == 0 else Decimal('5')  # First bond: 10 units, second: 5 units
                
                holding = Holding(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    bond_id=bond.id,
                    quantity=demo_quantity
                )
                db.add(holding)
            
            db.commit()
            print(f"Created demo holdings for new user {user.wallet_address}")
            return True
    
    except Exception as e:
        print(f"Error creating demo holdings: {e}")
        db.rollback()
        return False

# Pydantic models for request/response
class OrderCreate(BaseModel):
    bond_id: str
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(default="limit", pattern="^(limit|market)$")
    price: Decimal = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)

class PublicOrderCreate(BaseModel):
    bond_id: str
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(default="limit", pattern="^(limit|market)$")
    price: Decimal = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    user_wallet_address: str = Field(..., min_length=1)

class OrderResponse(BaseModel):
    id: str
    bond_id: str
    side: str
    order_type: str
    price: Decimal
    quantity: Decimal
    filled_quantity: Decimal
    status: str
    tx_hash: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class TradeResponse(BaseModel):
    id: str
    bond_id: str
    price: Decimal
    quantity: Decimal
    tx_hash: Optional[str]
    executed_at: datetime
    buyer_order_id: str
    seller_order_id: str

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kyc_verified)
):
    """Create a new trading order"""
    try:
        # Verify bond exists
        bond = db.query(Bond).filter(Bond.id == order_data.bond_id).first()
        if not bond:
            raise HTTPException(status_code=404, detail="Bond not found")

        # For sell orders, verify user has sufficient holdings
        if order_data.side == "sell":
            holding = db.query(Holding).filter(
                and_(
                    Holding.user_id == current_user.id,
                    Holding.bond_id == bond.id
                )
            ).first()
            
            if not holding or holding.quantity < order_data.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient holdings for sell order"
                )

        # Create order with transaction hash
        tx_hash = generate_mock_tx_hash()
        new_order = Order(
            id=uuid.uuid4(),
            user_id=current_user.id,
            bond_id=bond.id,
            side=order_data.side,
            type=order_data.order_type,
            price=order_data.price,
            quantity=order_data.quantity,
            status="open",
            tx_hash=tx_hash
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # Process order through matching engine
        matching_engine = MatchingEngine(db, manager)
        trades = matching_engine.process_order(new_order)
        
        # Refresh order to get updated status
        db.refresh(new_order)

        return OrderResponse(
            id=str(new_order.id),
            bond_id=str(new_order.bond_id),
            side=new_order.side,
            order_type=new_order.type,
            price=new_order.price,
            quantity=new_order.quantity,
            filled_quantity=new_order.filled_quantity,
            status=new_order.status,
            tx_hash=new_order.tx_hash,
            created_at=new_order.created_at,
            updated_at=new_order.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@router.post("/public/create", response_model=OrderResponse)
async def create_public_order(
    order_data: PublicOrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new trading order using wallet address (public endpoint, no authentication required)"""
    try:
        # Verify bond exists
        bond = db.query(Bond).filter(Bond.id == order_data.bond_id).first()
        if not bond:
            raise HTTPException(status_code=404, detail="Bond not found")

        # Get or create user by wallet address
        user = db.query(User).filter(User.wallet_address == order_data.user_wallet_address).first()
        if not user:
            # Auto-create user for this wallet address
            user = User(
                id=uuid.uuid4(),
                wallet_address=order_data.user_wallet_address,
                is_active=True,
                kyc_verified=True  # Auto-verify for wallet-based trading
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Give new user demo holdings so they can start trading
            create_demo_holdings_for_new_user(db, user)

        # For sell orders, verify user has sufficient holdings
        if order_data.side == "sell":
            holding = db.query(Holding).filter(
                and_(
                    Holding.user_id == user.id,
                    Holding.bond_id == bond.id
                )
            ).first()
            
            if not holding or holding.quantity < order_data.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient holdings for sell order"
                )

        # Create order with transaction hash
        tx_hash = generate_mock_tx_hash()
        new_order = Order(
            id=uuid.uuid4(),
            user_id=user.id,
            bond_id=bond.id,
            side=order_data.side,
            type=order_data.order_type,
            price=order_data.price,
            quantity=order_data.quantity,
            status="open",
            tx_hash=tx_hash
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # Process order through matching engine
        matching_engine = MatchingEngine(db, manager)
        trades = matching_engine.process_order(new_order)
        
        # Refresh order to get updated status
        db.refresh(new_order)

        return OrderResponse(
            id=str(new_order.id),
            bond_id=str(new_order.bond_id),
            side=new_order.side,
            order_type=new_order.type,
            price=new_order.price,
            quantity=new_order.quantity,
            filled_quantity=new_order.filled_quantity,
            status=new_order.status,
            tx_hash=new_order.tx_hash,
            created_at=new_order.created_at,
            updated_at=new_order.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    bond_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's orders with optional filtering"""
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    if bond_id:
        query = query.filter(Order.bond_id == bond_id)
    if status:
        query = query.filter(Order.status == status)
    if side:
        query = query.filter(Order.side == side)
    
    orders = query.order_by(desc(Order.created_at)).limit(limit).all()
    
    return [
        OrderResponse(
            id=str(order.id),
            bond_id=str(order.bond_id),
            side=order.side,
            order_type=order.type,
            price=order.price,
            quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            status=order.status,
            tx_hash=order.tx_hash,
            created_at=order.created_at,
            updated_at=order.updated_at
        )
        for order in orders
    ]

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific order by ID (user can only access their own orders)"""
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.user_id == current_user.id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(
        id=str(order.id),
        bond_id=str(order.bond_id),
        side=order.side,
        order_type=order.type,
        price=order.price,
        quantity=order.quantity,
        filled_quantity=order.filled_quantity,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.delete("/{order_id}")
async def cancel_order(
    order_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel an open order"""
    matching_engine = MatchingEngine(db, manager)
    success = matching_engine.cancel_order(uuid.UUID(order_id), current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel order (not found or not cancellable)"
        )
    
    return {"message": "Order cancelled successfully", "order_id": order_id}

@router.get("/trades/", response_model=List[TradeResponse])
async def get_trades(
    bond_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's trade history"""
    # Get user's order IDs
    user_order_ids = db.query(Order.id).filter(Order.user_id == current_user.id).subquery()
    
    # Find trades involving user's orders
    query = db.query(Trade).filter(
        or_(
            Trade.buy_order_id.in_(user_order_ids),
            Trade.sell_order_id.in_(user_order_ids)
        )
    )
    
    if bond_id:
        query = query.filter(Trade.bond_id == bond_id)
    
    trades = query.order_by(desc(Trade.executed_at)).limit(limit).all()
    
    return [
        TradeResponse(
            id=str(trade.id),
            bond_id=str(trade.bond_id),
            price=trade.price,
            quantity=trade.quantity,
            executed_at=trade.executed_at,
            buyer_order_id=str(trade.buy_order_id),
            seller_order_id=str(trade.sell_order_id)
        )
        for trade in trades
    ]

@router.get("/{bond_id}/orderbook")
async def get_orderbook(bond_id: str, db: Session = Depends(get_db)):
    """Get orderbook for a specific bond"""
    matching_engine = MatchingEngine(db, manager)
    orderbook = matching_engine.get_orderbook(uuid.UUID(bond_id))
    return orderbook

@router.get("/public/by-wallet", response_model=List[OrderResponse])
async def get_orders_by_wallet(
    wallet_address: str = Query(..., description="Wallet address to filter orders"),
    bond_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get orders by wallet address (public endpoint, no authentication required)"""
    # First find the user by wallet address
    user = db.query(User).filter(User.wallet_address == wallet_address).first()
    if not user:
        # Return empty list for non-existent users instead of error
        return []
    
    # Query orders for this user
    query = db.query(Order).filter(Order.user_id == user.id)
    
    if bond_id:
        query = query.filter(Order.bond_id == bond_id)
    if status:
        query = query.filter(Order.status == status)
    if side:
        query = query.filter(Order.side == side)
    
    orders = query.order_by(desc(Order.created_at)).limit(limit).all()
    
    return [
        OrderResponse(
            id=str(order.id),
            bond_id=str(order.bond_id),
            side=order.side,
            order_type=order.type,
            price=order.price,
            quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            status=order.status,
            tx_hash=order.tx_hash,
            created_at=order.created_at,
            updated_at=order.updated_at
        )
        for order in orders
    ]
