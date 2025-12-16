"""
Database models and connection management for PostgreSQL
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

# Database connection
# Render provides DATABASE_URL automatically (PostgreSQL)
# For local development, uses SQLite (no setup needed)
def get_database_url():
    """Get database URL from environment or use SQLite for local dev"""
    url = os.environ.get('DATABASE_URL')
    if not url:
        # Use SQLite for local development (no installation needed)
        url = 'sqlite:///quantify.db'
        print("ℹ️  Using SQLite for local development (no setup needed)")
        print("   For Render deployment, PostgreSQL is used automatically")
    return url

DATABASE_URL = get_database_url()

# Initialize engine and SessionLocal (will be created on first use if needed)
engine = None
SessionLocal = None

def create_engine_instance():
    """Create database engine instance"""
    url = get_database_url()  # Get fresh URL each time
    # SQLite needs different connection string format
    if url.startswith('sqlite'):
        return create_engine(url, echo=False, connect_args={'check_same_thread': False})
    else:
        # PostgreSQL connection - handle connection string format
        # Render provides DATABASE_URL in format: postgresql://user:pass@host:port/dbname
        # SQLAlchemy 2.0+ works with postgresql:// but psycopg2 is the driver
        if url.startswith('postgresql://') and '+psycopg2' not in url:
            # Convert to SQLAlchemy format with driver
            url = url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        return create_engine(url, echo=False, pool_pre_ping=True)

# Try to create engine at import time, but don't fail if it doesn't work
try:
    engine = create_engine_instance()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"⚠️  Warning: Database connection error at import: {e}")
    print("   Will retry on first use...")
    engine = None
    SessionLocal = None


class User(Base):
    """User accounts"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    reset_code = Column(String, nullable=True)  # 4-digit code
    reset_code_expires = Column(DateTime, nullable=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    portfolio_history = relationship("PortfolioHistory", back_populates="user", cascade="all, delete-orphan")
    portfolio_adjustments = relationship("PortfolioAdjustment", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """User sessions"""
    __tablename__ = 'sessions'
    
    session_token = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Relationship
    user = relationship("User")


class Trade(Base):
    """Trades"""
    __tablename__ = 'trades'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # BUY, SELL, OPEN, CLOSE
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    transaction_fee = Column(Float, default=0.0)
    sold_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    
    # Option fields
    option_type = Column(String, nullable=True)  # CALL, PUT
    strike = Column(Float, nullable=True)
    expiration = Column(String, nullable=True)
    trade_type = Column(String, nullable=True)  # OPTION, STOCK
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="trades")


class PortfolioHistory(Base):
    """Daily portfolio value history"""
    __tablename__ = 'portfolio_history'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_value = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="portfolio_history")


class PortfolioAdjustment(Base):
    """Portfolio adjustments (deposits/withdrawals)"""
    __tablename__ = 'portfolio_adjustments'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Positive for deposits, negative for withdrawals
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="portfolio_adjustments")


def init_db():
    """Initialize database tables"""
    global engine, SessionLocal
    try:
        if engine is None:
            engine = create_engine_instance()
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created/verified")
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")
        raise


def get_db():
    """Get database session"""
    global engine, SessionLocal
    # Recreate engine if it wasn't created at import time
    if engine is None or SessionLocal is None:
        engine = create_engine_instance()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def close_db(db):
    """Close database session"""
    try:
        if db:
            db.close()
    except:
        pass

