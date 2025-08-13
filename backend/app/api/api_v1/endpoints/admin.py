from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from app.db.database import get_db
from app.models.models import User, Bond, Order, Trade, Holding

router = APIRouter()

@router.post("/seed-data")
async def seed_sample_data(db: Session = Depends(get_db)):
    """Seed the database with sample data for testing"""
    try:
        # First, ensure the database schema is up to date
        from sqlalchemy import text
        try:
            # Check if tx_hash columns exist, add if missing
            connection = db.connection()
            
            # Check orders table
            result = connection.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = 'tx_hash'
            """))
            if not result.fetchone():
                connection.execute(text("ALTER TABLE orders ADD COLUMN tx_hash VARCHAR"))
                db.commit()
                print("Added tx_hash column to orders table during seeding")
            
            # Check trades table
            result = connection.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'trades' AND column_name = 'tx_hash'
            """))
            if not result.fetchone():
                connection.execute(text("ALTER TABLE trades ADD COLUMN tx_hash VARCHAR"))
                db.commit()
                print("Added tx_hash column to trades table during seeding")
                
        except Exception as schema_error:
            print(f"Schema update during seeding failed: {schema_error}")
            # Continue anyway, might work if columns already exist
        
        # Check if data already exists
        existing_user = db.query(User).filter(User.email == "trader1@example.com").first()
        if existing_user:
            # Data already exists, get counts and return
            user_count = db.query(User).count()
            bond_count = db.query(Bond).count()
            order_count = db.query(Order).count()
            trade_count = db.query(Trade).count()
            holding_count = db.query(Holding).count()
            
            return {
                "message": "Sample data already exists",
                "users_count": user_count,
                "bonds_count": bond_count,
                "orders_count": order_count,
                "trades_count": trade_count,
                "holdings_count": holding_count
            }
        
        # Create sample users
        user1 = User(
            id=uuid.uuid4(),
            email="trader1@example.com",
            hashed_password="hashed_password",
            name="John Trader",
            wallet_address="0x1234567890123456789012345678901234567890",
            role="investor"
        )
        
        user2 = User(
            id=uuid.uuid4(),
            email="trader2@example.com", 
            hashed_password="hashed_password",
            name="Jane Investor",
            wallet_address="0x0987654321098765432109876543210987654321",
            role="investor"
        )
        
        issuer = User(
            id=uuid.uuid4(),
            email="issuer@corp.com",
            hashed_password="hashed_password",
            name="Corporate Issuer",
            wallet_address="0x1111111111111111111111111111111111111111",
            role="issuer"
        )
        
        db.add_all([user1, user2, issuer])
        db.flush()
        
        # Create sample bonds
        bond1 = Bond(
            id=uuid.uuid4(),
            issuer_id=issuer.id,
            name="TechCorp 5Y Bond",
            isin="US123456789",
            coupon_rate=5.5,
            maturity_date=datetime.utcnow() + timedelta(days=365*5),
            face_value=Decimal('1000'),
            min_unit=Decimal('100'),
            status="active",
            total_token_supply=1000000
        )
        
        bond2 = Bond(
            id=uuid.uuid4(),
            issuer_id=issuer.id,
            name="GovBond 10Y Treasury",
            isin="US987654321",
            coupon_rate=3.2,
            maturity_date=datetime.utcnow() + timedelta(days=365*10),
            face_value=Decimal('1000'),
            min_unit=Decimal('50'),
            status="active",
            total_token_supply=5000000
        )
        
        bond3 = Bond(
            id=uuid.uuid4(),
            issuer_id=issuer.id,
            name="StartupCorp 3Y Bond",
            isin="US555666777",
            coupon_rate=7.8,
            maturity_date=datetime.utcnow() + timedelta(days=365*3),
            face_value=Decimal('500'),
            min_unit=Decimal('25'),
            status="active",
            total_token_supply=200000
        )
        
        db.add_all([bond1, bond2, bond3])
        db.flush()
        
        # Create sample orders
        orders = [
            # Buy orders for bond1
            Order(
                id=uuid.uuid4(),
                user_id=user1.id,
                bond_id=bond1.id,
                side="buy",
                type="limit",
                price=Decimal('98.50'),
                quantity=Decimal('10'),
                status="open"
            ),
            Order(
                id=uuid.uuid4(),
                user_id=user2.id,
                bond_id=bond1.id,
                side="buy",
                type="limit",
                price=Decimal('98.00'),
                quantity=Decimal('5'),
                status="open"
            ),
            # Sell orders for bond1
            Order(
                id=uuid.uuid4(),
                user_id=user1.id,
                bond_id=bond1.id,
                side="sell",
                type="limit",
                price=Decimal('99.50'),
                quantity=Decimal('8'),
                status="open"
            ),
            Order(
                id=uuid.uuid4(),
                user_id=user2.id,
                bond_id=bond1.id,
                side="sell",
                type="limit",
                price=Decimal('100.00'),
                quantity=Decimal('12'),
                status="open"
            ),
            
            # Orders for other bonds
            Order(
                id=uuid.uuid4(),
                user_id=user1.id,
                bond_id=bond2.id,
                side="buy",
                type="limit",
                price=Decimal('95.75'),
                quantity=Decimal('20'),
                status="open"
            ),
            Order(
                id=uuid.uuid4(),
                user_id=user2.id,
                bond_id=bond3.id,
                side="sell",
                type="limit",
                price=Decimal('102.25'),
                quantity=Decimal('15'),
                status="open"
            ),
        ]
        
        db.add_all(orders)
        db.flush()
        
        # Create some sample trades (historical)
        trade1 = Trade(
            id=uuid.uuid4(),
            buy_order_id=orders[0].id,
            sell_order_id=orders[2].id,
            bond_id=bond1.id,
            price=Decimal('99.00'),
            quantity=Decimal('5'),
            executed_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        trade2 = Trade(
            id=uuid.uuid4(),
            buy_order_id=orders[1].id,
            sell_order_id=orders[3].id,
            bond_id=bond1.id,
            price=Decimal('99.25'),
            quantity=Decimal('3'),
            executed_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        db.add_all([trade1, trade2])
        
        # Create sample holdings
        holding1 = Holding(
            id=uuid.uuid4(),
            user_id=user1.id,
            bond_id=bond1.id,
            quantity=Decimal('25')
        )
        
        holding2 = Holding(
            id=uuid.uuid4(),
            user_id=user2.id,
            bond_id=bond2.id,
            quantity=Decimal('40')
        )
        
        holding3 = Holding(
            id=uuid.uuid4(),
            user_id=user1.id,
            bond_id=bond3.id,
            quantity=Decimal('15')
        )
        
        db.add_all([holding1, holding2, holding3])
        
        db.commit()
        
        return {
            "message": "Sample data seeded successfully",
            "users_created": 3,
            "bonds_created": 3,
            "orders_created": len(orders),
            "trades_created": 2,
            "holdings_created": 3
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error seeding data: {str(e)}")

@router.delete("/clear-data")
async def clear_all_data(db: Session = Depends(get_db)):
    """Clear all data from database (for testing)"""
    try:
        # Delete in correct order due to foreign key constraints
        db.query(Trade).delete()
        db.query(Holding).delete()
        db.query(Order).delete()
        db.query(Bond).delete()
        db.query(User).delete()
        
        db.commit()
        
        return {"message": "All data cleared successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")
