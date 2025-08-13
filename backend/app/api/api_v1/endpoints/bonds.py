from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from app.db.database import get_db
from app.models.models import Bond, Order, Trade, Holding, User

router = APIRouter()

# Pydantic models
class BondCreate(BaseModel):
    name: str
    isin: str
    coupon_rate: float
    maturity_date: datetime
    face_value: Decimal
    min_unit: Decimal
    issuer_wallet_address: str

class BondResponse(BaseModel):
    id: str
    name: str
    isin: str
    coupon_rate: float
    maturity_date: datetime
    face_value: float
    min_unit: float
    status: str
    current_price: Optional[float]
    total_volume_24h: float
    price_change_24h: float
    price_change_percentage: float
    market_cap: float
    total_supply: Optional[int]

class OrderBookEntry(BaseModel):
    price: Decimal
    quantity: Decimal
    orders_count: int

class OrderBookResponse(BaseModel):
    bond_id: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    spread: Decimal
    mid_price: Decimal

class MarketStatsResponse(BaseModel):
    bond_id: str
    current_price: float
    volume_24h: float
    price_change_24h: float
    price_change_percentage: float
    high_24h: float
    low_24h: float
    trades_count_24h: int

@router.get("/", response_model=List[BondResponse])
async def get_bonds(
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get all bonds with market data"""
    query = db.query(Bond)
    
    if status:
        query = query.filter(Bond.status == status)
    
    bonds = query.limit(limit).all()
    result = []
    
    for bond in bonds:
        # Calculate current market price (last trade price)
        last_trade = db.query(Trade).filter(Trade.bond_id == bond.id).order_by(desc(Trade.executed_at)).first()
        current_price = last_trade.price if last_trade else bond.face_value
        
        # Calculate 24h volume
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        volume_24h = db.query(func.sum(Trade.quantity * Trade.price)).filter(
            and_(Trade.bond_id == bond.id, Trade.executed_at >= twenty_four_hours_ago)
        ).scalar() or Decimal('0')
        
        # Calculate price change
        price_24h_ago = db.query(Trade.price).filter(
            and_(Trade.bond_id == bond.id, Trade.executed_at <= twenty_four_hours_ago)
        ).order_by(desc(Trade.executed_at)).first()
        
        if price_24h_ago:
            price_change_24h = current_price - price_24h_ago[0]
            price_change_percentage = float((price_change_24h / price_24h_ago[0]) * 100)
        else:
            price_change_24h = Decimal('0')
            price_change_percentage = 0.0
        
        # Calculate market cap (total holdings * current price)
        total_holdings = db.query(func.sum(Holding.quantity)).filter(Holding.bond_id == bond.id).scalar() or Decimal('0')
        market_cap = total_holdings * current_price
        
        result.append(BondResponse(
            id=str(bond.id),
            name=bond.name,
            isin=bond.isin,
            coupon_rate=bond.coupon_rate,
            maturity_date=bond.maturity_date,
            face_value=float(bond.face_value),
            min_unit=float(bond.min_unit),
            status=bond.status,
            current_price=float(current_price),
            total_volume_24h=float(volume_24h),
            price_change_24h=float(price_change_24h),
            price_change_percentage=price_change_percentage,
            market_cap=float(market_cap),
            total_supply=bond.total_token_supply
        ))
    
    return result

@router.get("/{bond_id}", response_model=BondResponse)
async def get_bond(bond_id: str, db: Session = Depends(get_db)):
    """Get specific bond with market data"""
    bond = db.query(Bond).filter(Bond.id == bond_id).first()
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    
    # Same market data calculation as above
    last_trade = db.query(Trade).filter(Trade.bond_id == bond.id).order_by(desc(Trade.executed_at)).first()
    current_price = last_trade.price if last_trade else bond.face_value
    
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    volume_24h = db.query(func.sum(Trade.quantity * Trade.price)).filter(
        and_(Trade.bond_id == bond.id, Trade.executed_at >= twenty_four_hours_ago)
    ).scalar() or Decimal('0')
    
    price_24h_ago = db.query(Trade.price).filter(
        and_(Trade.bond_id == bond.id, Trade.executed_at <= twenty_four_hours_ago)
    ).order_by(desc(Trade.executed_at)).first()
    
    if price_24h_ago:
        price_change_24h = current_price - price_24h_ago[0]
        price_change_percentage = float((price_change_24h / price_24h_ago[0]) * 100)
    else:
        price_change_24h = Decimal('0')
        price_change_percentage = 0.0
    
    total_holdings = db.query(func.sum(Holding.quantity)).filter(Holding.bond_id == bond.id).scalar() or Decimal('0')
    market_cap = total_holdings * current_price
    
    return BondResponse(
        id=str(bond.id),
        name=bond.name,
        isin=bond.isin,
        coupon_rate=bond.coupon_rate,
        maturity_date=bond.maturity_date,
        face_value=float(bond.face_value),
        min_unit=float(bond.min_unit),
        status=bond.status,
        current_price=float(current_price),
        total_volume_24h=float(volume_24h),
        price_change_24h=float(price_change_24h),
        price_change_percentage=price_change_percentage,
        market_cap=float(market_cap),
        total_supply=bond.total_token_supply
    )

@router.get("/{bond_id}/orderbook", response_model=OrderBookResponse)
async def get_order_book(bond_id: str, db: Session = Depends(get_db)):
    """Get order book for a specific bond"""
    bond = db.query(Bond).filter(Bond.id == bond_id).first()
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    
    # Get buy orders (bids) grouped by price
    bids_query = db.query(
        Order.price,
        func.sum(Order.quantity - Order.filled_quantity).label('total_quantity'),
        func.count(Order.id).label('orders_count')
    ).filter(
        and_(
            Order.bond_id == bond_id,
            Order.side == 'buy',
            Order.status == 'open'
        )
    ).group_by(Order.price).order_by(desc(Order.price)).limit(10)
    
    bids = [
        OrderBookEntry(
            price=row.price,
            quantity=row.total_quantity,
            orders_count=row.orders_count
        )
        for row in bids_query.all()
    ]
    
    # Get sell orders (asks) grouped by price
    asks_query = db.query(
        Order.price,
        func.sum(Order.quantity - Order.filled_quantity).label('total_quantity'),
        func.count(Order.id).label('orders_count')
    ).filter(
        and_(
            Order.bond_id == bond_id,
            Order.side == 'sell',
            Order.status == 'open'
        )
    ).group_by(Order.price).order_by(Order.price).limit(10)
    
    asks = [
        OrderBookEntry(
            price=row.price,
            quantity=row.total_quantity,
            orders_count=row.orders_count
        )
        for row in asks_query.all()
    ]
    
    # Calculate spread and mid price
    best_bid = bids[0].price if bids else Decimal('0')
    best_ask = asks[0].price if asks else Decimal('0')
    spread = best_ask - best_bid if best_bid and best_ask else Decimal('0')
    mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else Decimal('0')
    
    return OrderBookResponse(
        bond_id=bond_id,
        bids=bids,
        asks=asks,
        spread=spread,
        mid_price=mid_price
    )

@router.get("/{bond_id}/stats", response_model=MarketStatsResponse)
async def get_market_stats(bond_id: str, db: Session = Depends(get_db)):
    """Get detailed market statistics for a bond"""
    bond = db.query(Bond).filter(Bond.id == bond_id).first()
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    # Current price (last trade)
    last_trade = db.query(Trade).filter(Trade.bond_id == bond_id).order_by(desc(Trade.executed_at)).first()
    current_price = last_trade.price if last_trade else bond.face_value
    
    # 24h volume
    volume_24h = db.query(func.sum(Trade.quantity * Trade.price)).filter(
        and_(Trade.bond_id == bond_id, Trade.executed_at >= twenty_four_hours_ago)
    ).scalar() or Decimal('0')
    
    # Price change
    price_24h_ago = db.query(Trade.price).filter(
        and_(Trade.bond_id == bond_id, Trade.executed_at <= twenty_four_hours_ago)
    ).order_by(desc(Trade.executed_at)).first()
    
    if price_24h_ago:
        price_change_24h = current_price - price_24h_ago[0]
        price_change_percentage = float((price_change_24h / price_24h_ago[0]) * 100)
    else:
        price_change_24h = Decimal('0')
        price_change_percentage = 0.0
    
    # High and low 24h
    price_stats = db.query(
        func.max(Trade.price).label('high_24h'),
        func.min(Trade.price).label('low_24h'),
        func.count(Trade.id).label('trades_count')
    ).filter(
        and_(Trade.bond_id == bond_id, Trade.executed_at >= twenty_four_hours_ago)
    ).first()
    
    high_24h = price_stats.high_24h if price_stats.high_24h else current_price
    low_24h = price_stats.low_24h if price_stats.low_24h else current_price
    trades_count_24h = price_stats.trades_count if price_stats.trades_count else 0
    
    return MarketStatsResponse(
        bond_id=bond_id,
        current_price=float(current_price),
        volume_24h=float(volume_24h),
        price_change_24h=float(price_change_24h),
        price_change_percentage=price_change_percentage,
        high_24h=float(high_24h),
        low_24h=float(low_24h),
        trades_count_24h=trades_count_24h
    )

@router.post("/", response_model=BondResponse)
async def create_bond(bond_data: BondCreate, db: Session = Depends(get_db)):
    """Create a new bond (for issuers)"""
    try:
        # Get or create issuer user
        issuer = db.query(User).filter(User.wallet_address == bond_data.issuer_wallet_address).first()
        if not issuer:
            issuer = User(
                id=uuid.uuid4(),
                email=f"{bond_data.issuer_wallet_address}@issuer.local",
                hashed_password="wallet_auth",
                name=f"Issuer_{bond_data.issuer_wallet_address[:8]}",
                wallet_address=bond_data.issuer_wallet_address,
                role="issuer"
            )
            db.add(issuer)
            db.flush()
        
        # Create bond
        new_bond = Bond(
            id=uuid.uuid4(),
            issuer_id=issuer.id,
            name=bond_data.name,
            isin=bond_data.isin,
            coupon_rate=bond_data.coupon_rate,
            maturity_date=bond_data.maturity_date,
            face_value=bond_data.face_value,
            min_unit=bond_data.min_unit,
            status="active"
        )
        
        db.add(new_bond)
        db.commit()
        db.refresh(new_bond)
        
        return BondResponse(
            id=str(new_bond.id),
            name=new_bond.name,
            isin=new_bond.isin,
            coupon_rate=new_bond.coupon_rate,
            maturity_date=new_bond.maturity_date,
            face_value=float(new_bond.face_value),
            min_unit=float(new_bond.min_unit),
            status=new_bond.status,
            current_price=float(new_bond.face_value),
            total_volume_24h=0.0,
            price_change_24h=0.0,
            price_change_percentage=0.0,
            market_cap=0.0,
            total_supply=new_bond.total_token_supply
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating bond: {str(e)}")
