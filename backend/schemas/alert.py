from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum
from backend.utils.validators import Validators

class AlertSeverityEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertTypeEnum(str, Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    PROCESS = "PROCESS"
    SSH = "SSH"
    SERVICE = "SERVICE"

class AlertBase(BaseModel):
    server_id: int = Field(..., gt=0, description="Server ID")
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    severity: AlertSeverityEnum = Field(..., description="Alert severity")
    message: str = Field(..., min_length=1, max_length=1000, description="Alert message")
    value: float = Field(..., ge=0, description="Current metric value")
    threshold: float = Field(..., ge=0, description="Threshold value")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if Validators.is_sql_injection_attempt(v):
            raise ValueError("Potential SQL injection detected in message")
        
        sanitized = Validators.sanitize_string(v, max_length=1000)
        if not sanitized.strip():
            raise ValueError("Message cannot be empty after sanitization")
        
        return sanitized
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: float) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid number")
    
    @field_validator('threshold')
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            raise ValueError("Threshold must be a valid number")

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    is_acknowledged: Optional[bool] = None
    is_resolved: Optional[bool] = None

class AlertResponse(AlertBase):
    id: int
    is_acknowledged: bool
    is_resolved: bool
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True