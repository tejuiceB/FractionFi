from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Try PostgreSQL first, fallback to SQLite
try:
    engine = create_engine(settings.DATABASE_URL)
    # Test connection
    engine.connect()
    logger.info("Connected to PostgreSQL database")
except Exception as e:
    logger.warning(f"Failed to connect to PostgreSQL: {e}")
    logger.info("Falling back to SQLite database")
    engine = create_engine(settings.DATABASE_URL_FALLBACK, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
