#!/usr/bin/env python3
"""
Migration script to add reset_token and reset_token_expires columns to users table
"""
from database import get_db, engine
from sqlalchemy import text

def migrate():
    """Add reset_token and reset_token_expires columns if they don't exist"""
    db = get_db()
    try:
        # Check if columns exist (SQLite specific)
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if 'reset_token' not in columns:
            print("Adding reset_token column...")
            db.execute(text("ALTER TABLE users ADD COLUMN reset_token TEXT"))
            print("✓ Added reset_token column")
        else:
            print("✓ reset_token column already exists")
        
        if 'reset_token_expires' not in columns:
            print("Adding reset_token_expires column...")
            db.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME"))
            print("✓ Added reset_token_expires column")
        else:
            print("✓ reset_token_expires column already exists")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration error: {e}")
        # Try PostgreSQL syntax if SQLite fails
        try:
            if 'reset_token' not in columns:
                db.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR"))
            if 'reset_token_expires' not in columns:
                db.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP"))
            db.commit()
            print("✅ Migration completed with PostgreSQL syntax!")
        except Exception as e2:
            print(f"❌ PostgreSQL migration also failed: {e2}")
            raise
    finally:
        db.close()

if __name__ == '__main__':
    migrate()

