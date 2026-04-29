from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.models.database import Base
from backend.models.alert import AlertType, AlertSeverity

class AlertConfig(Base):
    __tablename__ = "alert_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), index=True)
    metric_type = Column(Enum(AlertType), index=True)
    threshold_value = Column(Float)
    comparison_operator = Column(String(10))
    severity = Column(Enum(AlertSeverity))
    enabled = Column(Boolean, default=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    server = relationship("Server", back_populates="alert_configs")