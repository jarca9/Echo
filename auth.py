"""
User Authentication System for Echo Trading Journal
Now using PostgreSQL database
"""
import hashlib
import secrets
import os
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
    
    def send_reset_code_email(self, email: str, code: str) -> bool:
        """Send password reset code via email"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get email settings from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        from_email = os.environ.get('FROM_EMAIL', smtp_user)
        
        # If no email configured, just print to console (for development)
        if not smtp_user or not smtp_password:
            print(f"[EMAIL] Password reset code for {email}: {code}")
            print("[EMAIL] Configure SMTP_USER and SMTP_PASSWORD environment variables to send real emails")
            return False  # Return False to indicate email was not sent
        
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = email
            msg['Subject'] = 'Echo Trading Journal - Password Reset Code'
            
            # Create a nicer HTML email
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #6c5ce7;">Password Reset Code</h2>
                        <p>You requested to reset your password for your Echo Trading Journal account.</p>
                        <div style="background-color: #f4f4f4; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                            <p style="font-size: 14px; color: #666; margin: 0 0 10px 0;">Your reset code is:</p>
                            <p style="font-size: 32px; font-weight: bold; color: #6c5ce7; letter-spacing: 4px; margin: 0;">{code}</p>
                        </div>
                        <p style="color: #666; font-size: 14px;">This code will expire in <strong>10 minutes</strong>.</p>
                        <p style="color: #666; font-size: 14px;">If you didn't request this password reset, please ignore this email.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px;">This is an automated message from Echo Trading Journal.</p>
                    </div>
                </body>
            </html>
            """
            
            # Plain text version for email clients that don't support HTML
            text_body = f"""
Password Reset Code

You requested to reset your password for your Echo Trading Journal account.

Your reset code is: {code}

This code will expire in 10 minutes.

If you didn't request this password reset, please ignore this email.

---
This is an automated message from Echo Trading Journal.
            """
            
            # Attach both HTML and plain text versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"[EMAIL] Password reset code sent successfully to {email}")
            return True
        except Exception as e:
            print(f"[EMAIL] Error sending email to {email}: {e}")
            import traceback
            traceback.print_exc()
            # Return False to indicate email sending failed
            return False
    
    def request_password_reset(self, email: str) -> Dict:
        """Generate a 4-digit password reset code and send via email"""
        email = email.lower().strip()
        db = get_db()
        
        try:
            user = db.query(User).filter(User.email == email).first()
            
            # Always return success to prevent email enumeration
            if not user:
                # Still generate a dummy code to keep timing similar
                reset_code = f"{secrets.randbelow(10000):04d}"
                return {
                    'success': True,
                    'message': 'A 4-digit reset code has been sent to your email. Please check your inbox.',
                    'reset_code': reset_code  # For consistent frontend behavior
                }
            
            # Generate 4-digit code
            reset_code = f"{secrets.randbelow(10000):04d}"
            expires_at = datetime.utcnow() + timedelta(minutes=10)  # Code expires in 10 minutes
            
            user.reset_code = reset_code
            user.reset_code_expires = expires_at
            
            db.commit()
            
            # Send email with code
            email_sent = self.send_reset_code_email(email, reset_code)
            
            # Only include reset_code in response if email is NOT configured (for development/testing)
            # This prevents exposing codes in production
            response = {
                'success': True,
                'message': 'A 4-digit reset code has been sent to your email. Please check your inbox.'
            }
            
            # Only include code in response if email sending failed/not configured
            if not email_sent or not os.environ.get('SMTP_USER') or not os.environ.get('SMTP_PASSWORD'):
                response['reset_code'] = reset_code
                response['message'] = f'A 4-digit reset code has been generated. Code: {reset_code} (Email not configured - check console or use this code)'
            
            return response
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            close_db(db)
    
    def verify_reset_code(self, email: str, code: str) -> Dict:
        """Verify the reset code"""
        email = email.lower().strip()
        db = get_db()
        
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid email or code'}
            
            if not user.reset_code or user.reset_code != code:
                return {'success': False, 'error': 'Invalid reset code'}
            
            # Check if code expired
            if user.reset_code_expires and datetime.utcnow() > user.reset_code_expires:
                user.reset_code = None
                user.reset_code_expires = None
                db.commit()
                return {'success': False, 'error': 'Reset code has expired. Please request a new one.'}
            
            return {'success': True, 'message': 'Code verified successfully'}
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            close_db(db)
    
    def reset_password(self, email: str, reset_code: str, new_password: str) -> Dict:
        """Reset a user's password using email and reset code"""
        if not email or not reset_code or not new_password:
            return {'success': False, 'error': 'Email, reset code, and new password are required'}
        
        if len(new_password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters'}
        
        email = email.lower().strip()
        db = get_db()
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid email or code'}
            
            # Store user ID for verification after update
            user_id = user.id
            user_email = user.email
            
            if not user.reset_code or user.reset_code != reset_code:
                return {'success': False, 'error': 'Invalid reset code'}
            
            # Check if code expired
            if user.reset_code_expires and datetime.utcnow() > user.reset_code_expires:
                user.reset_code = None
                user.reset_code_expires = None
                db.commit()
                return {'success': False, 'error': 'Reset code has expired. Please request a new one.'}
            
            # Update password and clear reset code (ONLY these fields)
            user.password_hash = self.hash_password(new_password)
            user.reset_code = None
            user.reset_code_expires = None
            
            db.commit()
            
            # Verify user still exists after commit
            db.refresh(user)
            if not user or user.id != user_id:
                print(f"ERROR: User account issue after password reset for {email}")
                db.rollback()
                return {'success': False, 'error': 'Account verification failed. Please contact support.'}
            
            return {'success': True, 'message': 'Password reset successfully'}
        except Exception as e:
            db.rollback()
            print(f"ERROR in reset_password for {email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'Database error: {str(e)}'}
        finally:
            close_db(db)
