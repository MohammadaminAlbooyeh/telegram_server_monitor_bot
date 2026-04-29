from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class MetricBase(BaseModel):
    server_id: int
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    memory_available: float
    disk_usage: float = Field(ge=0, le=100)
    disk_available: float
    network_in: float = 0.0
    network_out: float = 0.0
    load_average_1: float = 0.0
    load_average_5: float = 0.0
    load_average_15: float = 0.0
    temperature: Optional[float] = None

class MetricCreate(MetricBase):
    timestamp: Optional[datetime] = None

class MetricResponse(MetricBase):
    id: int
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class MetricHistory(BaseModel):
    timestamps: List[datetime]
    cpu_values: List[float]
    memory_values: List[float]
    disk_values: List[float]