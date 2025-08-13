import sys
sys.path.append('.')

from app.db.database import engine
from app.models.models import Base

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")

# Print created tables
print("\nCreated tables:")
for table_name in Base.metadata.tables.keys():
    print(f"  - {table_name}")
