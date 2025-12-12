#!/usr/bin/env python3
"""
Migrate users from users.json to database
"""
import json
import os
from datetime import datetime
from database import get_db, close_db, User
from auth import AuthManager

def migrate_users():
    """Migrate users from JSON to database"""
    users_file = 'users.json'
    
    if not os.path.exists(users_file):
        print("No users.json found - nothing to migrate")
        return
    
    # Load existing users
    with open(users_file, 'r') as f:
        users_data = json.load(f)
    
    db = get_db()
    auth_manager = AuthManager()
    migrated = 0
    skipped = 0
    
    try:
        for email, user_data in users_data.items():
            email = email.lower().strip()
            
            # Check if user already exists in database
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                print(f"⏭️  User {email} already exists in database - skipping")
                skipped += 1
                continue
            
            # Create user in database
            new_user = User(
                id=user_data['id'],
                email=email,
                name=user_data['name'],
                password_hash=user_data['password_hash'],
                created_at=datetime.fromisoformat(user_data['created_at']) if 'created_at' in user_data else datetime.utcnow(),
                last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
            )
            
            db.add(new_user)
            migrated += 1
            print(f"✅ Migrated user: {email} ({user_data['name']})")
        
        db.commit()
        print(f"\n✓ Migration complete!")
        print(f"  Migrated: {migrated} users")
        print(f"  Skipped: {skipped} users (already exist)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error migrating users: {e}")
        raise
    finally:
        close_db(db)

if __name__ == '__main__':
    print("🔄 Migrating users from users.json to database...")
    print("")
    migrate_users()

