from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class AlertTypeEnum(str, Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    PROCESS = "PROCESS"
    SSH = "SSH"
    SERVICE = "SERVICE"

class AlertSeverityEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertConfigBase(BaseModel):
    server_id: int
    metric_type: AlertTypeEnum
    threshold_value: float
    comparison_operator: str = Field(..., regex="^(>|<|>=|<=|==)$")
    severity: AlertSeverityEnum
    enabled: bool = True
    description: Optional[str] = None

class AlertConfigCreate(AlertConfigBase):
    pass

class AlertConfigUpdate(BaseModel):
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None
    severity: Optional[AlertSeverityEnum] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None

class AlertConfigResponse(AlertConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True