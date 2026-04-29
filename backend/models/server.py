from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.models.database import Base

class Server(Base):
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    hostname = Column(String(255), index=True)
    ssh_port = Column(Integer, default=22)
    username = Column(String(255))
    password = Column(String(255), nullable=True)
    ssh_key_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_check = Column(DateTime, nullable=True)
    
    # Relationships
    metrics = relationship("Metric", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="server", cascade="all, delete-orphan")
    alert_configs = relationship("AlertConfig", back_populates="server", cascade="all, delete-orphan")