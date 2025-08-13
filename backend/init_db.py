#!/usr/bin/env python3
"""
Database initialization script for FractionFi
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import engine, Base
from app.models.models import *  # Import all models to register them
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Create all database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # Test database connection
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            # Simple query to test connection
            db.execute("SELECT 1")
            logger.info("Database connection test successful!")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False
    return True

if __name__ == "__main__":
    logger.info("Initializing FractionFi database...")
    success = init_db()
    if success:
        logger.info("Database initialization completed successfully!")
    else:
        logger.error("Database initialization failed!")
        sys.exit(1)
