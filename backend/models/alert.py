from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.models.database import Base

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertType(str, enum.Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    PROCESS = "PROCESS"
    SSH = "SSH"
    SERVICE = "SERVICE"

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), index=True)
    alert_type = Column(Enum(AlertType), index=True)
    severity = Column(Enum(AlertSeverity), index=True)
    message = Column(Text)
    value = Column(Float)
    threshold = Column(Float)
    is_acknowledged = Column(Boolean, default=False, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationship
    server = relationship("Server", back_populates="alerts")