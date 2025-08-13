import sys
import os
sys.path.append('.')

try:
    from app.db.database import engine
    from app.models.models import Base
    
    print("🔗 Testing database connection...")
    
    # Test connection
    with engine.connect() as conn:
        print("✅ Database connection successful!")
        
        # Check if tables exist
        from sqlalchemy import text
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        
        tables = [row[0] for row in result]
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
        else:
            print("📝 No tables found. Creating tables...")
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully!")
        
except Exception as e:
    print(f"❌ Database Error: {e}")
    print("🔧 Make sure PostgreSQL container is running:")
    print("   docker ps | findstr postgres")
