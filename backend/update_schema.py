#!/usr/bin/env python3
"""
Database schema update script to add tx_hash columns
"""
import sys
sys.path.append('.')

from sqlalchemy import text
from app.db.database import engine

def update_database_schema():
    """Add tx_hash columns to orders and trades tables"""
    try:
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            
            try:
                # Check if tx_hash column exists in orders table
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='orders' AND column_name='tx_hash'
                """))
                
                if not result.fetchone():
                    print("Adding tx_hash column to orders table...")
                    connection.execute(text("""
                        ALTER TABLE orders ADD COLUMN tx_hash VARCHAR;
                    """))
                    print("✅ Added tx_hash column to orders table")
                else:
                    print("tx_hash column already exists in orders table")
                
                # Check if tx_hash column exists in trades table
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='trades' AND column_name='tx_hash'
                """))
                
                if not result.fetchone():
                    print("Adding tx_hash column to trades table...")
                    connection.execute(text("""
                        ALTER TABLE trades ADD COLUMN tx_hash VARCHAR;
                    """))
                    print("✅ Added tx_hash column to trades table")
                else:
                    print("tx_hash column already exists in trades table")
                
                # Commit the transaction
                trans.commit()
                print("🚀 Database schema update completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    update_database_schema()
