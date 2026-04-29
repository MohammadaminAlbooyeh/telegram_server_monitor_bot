from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.models.database import Base

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    memory_available = Column(Float, default=0.0)
    disk_usage = Column(Float, default=0.0)
    disk_available = Column(Float, default=0.0)
    network_in = Column(Float, default=0.0)
    network_out = Column(Float, default=0.0)
    load_average_1 = Column(Float, default=0.0)
    load_average_5 = Column(Float, default=0.0)
    load_average_15 = Column(Float, default=0.0)
    temperature = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    server = relationship("Server", back_populates="metrics")