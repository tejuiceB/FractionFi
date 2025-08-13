import sys
sys.path.append('.')

try:
    from app.db.database import engine
    print("✅ Database import successful")
    print(f"Database URL: {engine.url}")
    
    # Test connection
    with engine.connect() as conn:
        print("✅ Database connection successful")
        
    from app.models.models import Base
    print("✅ Models import successful")
    print(f"Tables to create: {list(Base.metadata.tables.keys())}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
