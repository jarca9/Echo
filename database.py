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
# Render provides DATABASE_URL automatically
# For local development, set DATABASE_URL environment variable or install PostgreSQL
# Example: export DATABASE_URL="postgresql://user:password@localhost/quantify"
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Fallback for local development (requires PostgreSQL installed)
    DATABASE_URL = 'postgresql://localhost/quantify'
    print("⚠ Warning: DATABASE_URL not set. Using default local PostgreSQL.")
    print("   For local development, install PostgreSQL and set DATABASE_URL")
    print("   For Render deployment, DATABASE_URL is set automatically")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """User accounts"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
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
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    return SessionLocal()


def close_db(db):
    """Close database session"""
    try:
        if db:
            db.close()
    except:
        pass

