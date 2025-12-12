"""
User Authentication System for Echo Trading Journal
Now using PostgreSQL database
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from database import get_db, close_db, User, Session

class AuthManager:
    """Manages user authentication and sessions using PostgreSQL"""
    
    def __init__(self):
        pass  # No initialization needed, database handles it
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode('utf-8'))
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a hash"""
        try:
            salt, hash_value = hashed.split(':')
            hash_obj = hashlib.sha256()
            hash_obj.update((password + salt).encode('utf-8'))
            return hash_obj.hexdigest() == hash_value
        except:
            return False
    
    def create_user(self, email: str, password: str, name: str) -> Dict:
        """Create a new user account"""
        email = email.lower().strip()
        db = get_db()
        
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return {'success': False, 'error': 'Email already registered'}
            
            # Validate email format
            if '@' not in email or '.' not in email.split('@')[1]:
                return {'success': False, 'error': 'Invalid email format'}
            
            # Validate password
            if len(password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}
            
            # Validate name
            if not name or len(name.strip()) < 2:
                return {'success': False, 'error': 'Name must be at least 2 characters'}
            
            # Create user
            user_id = secrets.token_urlsafe(16)
            new_user = User(
                id=user_id,
                email=email,
                name=name.strip(),
                password_hash=self.hash_password(password),
                created_at=datetime.utcnow(),
                last_login=None
            )
            
            db.add(new_user)
            db.commit()
            
            return {'success': True, 'user_id': user_id, 'email': email, 'name': name}
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            close_db(db)
    
    def sign_in(self, email: str, password: str) -> Dict:
        """Sign in a user"""
        email = email.lower().strip()
        db = get_db()
        
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid email or password'}
            
            if not self.verify_password(password, user.password_hash):
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            new_session = Session(
                session_token=session_token,
                user_id=user.id,
                email=email,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            db.add(new_session)
            db.commit()
            
            return {
                'success': True,
                'session_token': session_token,
                'user': {
                    'id': user.id,
                    'email': email,
                    'name': user.name
                }
            }
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            close_db(db)
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify a session token and return user info"""
        if not session_token:
            return None
        
        db = get_db()
        try:
            session = db.query(Session).filter(Session.session_token == session_token).first()
            
            if not session:
                return None
            
            # Check if session expired
            if datetime.utcnow() > session.expires_at:
                # Remove expired session
                db.delete(session)
                db.commit()
                return None
            
            # Get user
            user = db.query(User).filter(User.id == session.user_id).first()
            if not user:
                return None
            
            return {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        except Exception as e:
            return None
        finally:
            close_db(db)
    
    def sign_out(self, session_token: str) -> bool:
        """Sign out a user by removing their session"""
        if not session_token:
            return False
        
        db = get_db()
        try:
            session = db.query(Session).filter(Session.session_token == session_token).first()
            if session:
                db.delete(session)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            return False
        finally:
            close_db(db)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user info by email (without password)"""
        email = email.lower().strip()
        db = get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            return None
        except Exception as e:
            return None
        finally:
            close_db(db)
    
    def update_user_name(self, user_id: str, new_name: str) -> Dict:
        """Update user's name"""
        if not new_name or len(new_name.strip()) < 2:
            return {'success': False, 'error': 'Name must be at least 2 characters'}
        
        db = get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            user.name = new_name.strip()
            db.commit()
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            close_db(db)
