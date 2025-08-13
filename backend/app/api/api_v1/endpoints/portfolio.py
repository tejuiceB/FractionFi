from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
import uuid

from app.db.database import get_db
from app.services.portfolio import PortfolioService
from app.models.models import User, Bond, Holding

router = APIRouter()

def create_demo_holdings_for_new_user(db: Session, user: User):
    """Create demo holdings for a new user to enable trading"""
    try:
        print(f"🏗️ Creating demo holdings for user {user.wallet_address}")
        
        # Check if user already has holdings
        existing_holdings = db.query(Holding).filter(Holding.user_id == user.id).first()
        if existing_holdings:
            print(f"✅ User {user.wallet_address} already has holdings, skipping creation")
            return True  # User already has holdings
        
        # Get first 2 available bonds
        available_bonds = db.query(Bond).filter(Bond.status == "active").limit(2).all()
        print(f"📋 Found {len(available_bonds)} active bonds")
        
        if available_bonds:
            holdings_created = 0
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
                holdings_created += 1
                print(f"  ➕ Created holding: {bond.name} - {demo_quantity} units")
            
            db.commit()
            print(f"✅ Successfully created {holdings_created} demo holdings for user {user.wallet_address}")
            return True
        else:
            print(f"⚠️ No active bonds found to create holdings from")
            return False
    
    except Exception as e:
        print(f"❌ Error creating demo holdings: {e}")
        db.rollback()
        return False

class PortfolioHolding(BaseModel):
    bond_id: str
    bond_name: str
    isin: str
    quantity: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    pnl_percentage: float
    coupon_rate: float
    maturity_date: str

class PortfolioResponse(BaseModel):
    user_id: str
    wallet_address: str
    total_portfolio_value: float
    holdings: List[PortfolioHolding]
    holdings_count: int

class TradeHistoryItem(BaseModel):
    trade_id: str
    bond_name: str
    isin: str
    side: str
    price: float
    quantity: float
    total_value: float
    executed_at: str
    tx_hash: Optional[str]

class PerformanceMetrics(BaseModel):
    period_days: int
    trading_volume: float
    trade_count: int
    current_portfolio_value: float
    holdings_count: int

@router.get("/{wallet_address}", response_model=PortfolioResponse)
async def get_portfolio(wallet_address: str, db: Session = Depends(get_db)):
    """Get user's complete portfolio"""
    portfolio_service = PortfolioService(db)
    portfolio_data = portfolio_service.get_user_portfolio(wallet_address)
    
    # If user doesn't exist, create them automatically
    if "error" in portfolio_data and portfolio_data["error"] == "User not found":
        # Create new user with wallet address
        new_user = User(
            wallet_address=wallet_address,
            email=f"{wallet_address}@fractionfi.com",  # Temporary email
            hashed_password="wallet_auth",  # Placeholder for wallet auth
            name="Wallet User",  # Default name
            role="investor",
            kyc_status="pending"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Give new user demo holdings so they can start trading
        create_demo_holdings_for_new_user(db, new_user)
        
        # Get the portfolio again with the new holdings
        portfolio_data = portfolio_service.get_user_portfolio(wallet_address)
    
    # If user exists but has no holdings, give them demo holdings
    elif "error" not in portfolio_data and portfolio_data.get("holdings_count", 0) == 0:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if user:
            print(f"User {wallet_address} exists but has no holdings, creating demo holdings...")
            create_demo_holdings_for_new_user(db, user)
            # Get the portfolio again with the new holdings
            portfolio_data = portfolio_service.get_user_portfolio(wallet_address)
    
    # Handle any remaining errors
    if "error" in portfolio_data:
        # If it's still an error, try to create user and holdings as fallback
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            # Create new user as final fallback
            user = User(
                wallet_address=wallet_address,
                email=f"{wallet_address}@fractionfi.com",
                hashed_password="wallet_auth",
                name="Wallet User",
                role="investor",
                kyc_status="pending"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        create_demo_holdings_for_new_user(db, user)
        portfolio_data = portfolio_service.get_user_portfolio(wallet_address)
        
        if "error" in portfolio_data:
            # Final fallback - return empty portfolio but log the error
            print(f"Error getting portfolio for {wallet_address}: {portfolio_data.get('error', 'Unknown error')}")
            return PortfolioResponse(
                user_id=str(user.id) if user else "unknown",
                wallet_address=wallet_address,
                total_portfolio_value=0.0,
                holdings=[],
                holdings_count=0
            )
    
    # Success case - format and return the portfolio
    holdings = [
        PortfolioHolding(**holding) for holding in portfolio_data["holdings"]
    ]
    
    return PortfolioResponse(
        user_id=portfolio_data["user_id"],
        wallet_address=portfolio_data["wallet_address"],
        total_portfolio_value=portfolio_data["total_portfolio_value"],
        holdings=holdings,
        holdings_count=portfolio_data["holdings_count"]
    )

@router.get("/{wallet_address}/trades", response_model=List[TradeHistoryItem])
async def get_trade_history(
    wallet_address: str, 
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get user's trade history"""
    portfolio_service = PortfolioService(db)
    trades = portfolio_service.get_user_trade_history(wallet_address, limit)
    
    return [TradeHistoryItem(**trade) for trade in trades]

@router.get("/{wallet_address}/performance", response_model=PerformanceMetrics)
async def get_performance(
    wallet_address: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get user's portfolio performance metrics"""
    portfolio_service = PortfolioService(db)
    performance = portfolio_service.get_portfolio_performance(wallet_address, days)
    
    if "error" in performance:
        raise HTTPException(status_code=404, detail=performance["error"])
    
    return PerformanceMetrics(**performance)

@router.post("/{wallet_address}/demo-holdings")
async def create_demo_holdings(wallet_address: str, db: Session = Depends(get_db)):
    """Force create demo holdings for testing purposes"""
    try:
        # Get or create user
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            user = User(
                wallet_address=wallet_address,
                email=f"{wallet_address}@fractionfi.com",
                hashed_password="wallet_auth",
                name="Wallet User",
                role="investor",
                kyc_status="pending"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Clear existing holdings first
        db.query(Holding).filter(Holding.user_id == user.id).delete()
        db.commit()
        
        # Create new demo holdings
        success = create_demo_holdings_for_new_user(db, user)
        
        if success:
            # Return updated portfolio
            portfolio_service = PortfolioService(db)
            portfolio_data = portfolio_service.get_user_portfolio(wallet_address)
            return {
                "message": "Demo holdings created successfully",
                "portfolio": portfolio_data
            }
        else:
            return {
                "message": "Failed to create demo holdings",
                "error": "No active bonds available or other error"
            }
    
    except Exception as e:
        return {
            "message": "Error creating demo holdings",
            "error": str(e)
        }
