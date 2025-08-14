
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os

from config import Config
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

Base = declarative_base()
SessionLocal = scoped_session(sessionmaker(bind=engine))

def get_db_session():
    """Get a thread-safe database session."""
    return SessionLocal()

def close_db_session():
    """Close the scoped session."""
    SessionLocal.remove()
