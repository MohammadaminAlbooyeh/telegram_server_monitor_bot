from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from backend.models.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(String(255), unique=True, index=True)
    telegram_username = Column(String(255), nullable=True)
    telegram_first_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    notification_enabled = Column(Boolean, default=True)
    notification_quiet_start = Column(Integer, default=22)
    notification_quiet_end = Column(Integer, default=8)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, nullable=True)