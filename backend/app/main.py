from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.api_v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting FractionFi API...")
    
    # Ensure database schema is up to date
    try:
        from app.db.database import engine
        from sqlalchemy import text
        import time
        
        print("🔧 Checking and updating database schema...")
        
        # Try multiple times with different connection approaches
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with engine.connect() as connection:
                    # Use autocommit mode
                    connection = connection.execution_options(autocommit=True)
                    
                    # Force check if tx_hash column exists in orders table
                    print(f"Attempt {attempt + 1}: Checking orders table schema...")
                    result = connection.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'orders' AND column_name = 'tx_hash'
                    """))
                    
                    if result.fetchone():
                        print("✅ tx_hash column exists in orders table")
                    else:
                        print("❌ tx_hash column missing in orders table. Adding...")
                        connection.execute(text("ALTER TABLE orders ADD COLUMN tx_hash VARCHAR"))
                        print("✅ Added tx_hash column to orders table")
                    
                    # Check trades table
                    print(f"Attempt {attempt + 1}: Checking trades table schema...")
                    result = connection.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'trades' AND column_name = 'tx_hash'
                    """))
                    
                    if result.fetchone():
                        print("✅ tx_hash column exists in trades table")
                    else:
                        print("❌ tx_hash column missing in trades table. Adding...")
                        connection.execute(text("ALTER TABLE trades ADD COLUMN tx_hash VARCHAR"))
                        print("✅ Added tx_hash column to trades table")
                    
                    # Test that we can actually query the new columns
                    print("🧪 Testing new schema...")
                    connection.execute(text("SELECT tx_hash FROM orders LIMIT 1"))
                    connection.execute(text("SELECT tx_hash FROM trades LIMIT 1"))
                    print("✅ Schema validation successful!")
                    break
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    print(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("❌ All schema update attempts failed")
                    raise e
                
    except Exception as e:
        print(f"⚠️ Database schema update failed: {e}")
        print("The application will continue but some features may not work correctly")
    
    yield
    
    # Shutdown
    print("Shutting down FractionFi API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Tokenized Bond Liquidity Platform API",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "FractionFi Bond Liquidity Platform API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fractionfi-api"}
