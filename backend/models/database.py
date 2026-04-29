from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import DATABASE_URL, DATABASE_ECHO
import enum

# Database Engine
engine = create_engine(DATABASE_URL, echo=DATABASE_ECHO, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Import models so they are registered with SQLAlchemy metadata and can be re-exported
from backend.models.server import Server
from backend.models.metric import Metric
from backend.models.alert import Alert
from backend.models.user import User
from backend.models.alert_config import AlertConfig
