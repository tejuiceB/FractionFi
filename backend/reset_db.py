#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

from app.db.database import engine
from app.models.models import Base

# Remove existing database file if it exists
db_file = "fractionfi.db"
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Removed existing database file: {db_file}")

# Create all tables with new schema
print("Creating database tables with updated schema...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")

# Print created tables
print("\nCreated tables:")
for table_name in Base.metadata.tables.keys():
    print(f"  - {table_name}")

print("\n🚀 Database reset complete! Ready for fresh data.")
