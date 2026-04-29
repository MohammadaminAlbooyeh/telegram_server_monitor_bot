from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from backend.utils.validators import Validators

class ServerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Server name")
    hostname: str = Field(..., min_length=1, max_length=255, description="Hostname or IP address")
    ssh_port: int = Field(default=22, ge=1, le=65535, description="SSH port")
    username: str = Field(..., min_length=1, max_length=255, description="SSH username")
    password: Optional[str] = Field(None, max_length=1000, description="SSH password")
    ssh_key_path: Optional[str] = Field(None, max_length=4096, description="Path to SSH private key")
    description: Optional[str] = Field(None, max_length=2000, description="Server description")
    is_active: bool = Field(True, description="Whether server is active")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        is_valid, sanitized = Validators.validate_and_sanitize_name(v)
        if not is_valid:
            raise ValueError("Invalid name format or potential injection attempt")
        
        return sanitized
    
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        if not Validators.validate_hostname(v):
            raise ValueError("Invalid hostname or IP address format")
        
        if Validators.is_sql_injection_attempt(v):
            raise ValueError("Potential SQL injection detected in hostname")
        
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not Validators.validate_username(v):
            raise ValueError("Invalid username format. Must be 3-32 characters, alphanumeric with -_.")
        
        if Validators.is_sql_injection_attempt(v):
            raise ValueError("Potential SQL injection detected in username")
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        if len(v) > 1000:
            raise ValueError("Password too long")
        
        if Validators.is_sql_injection_attempt(v):
            raise ValueError("Potential SQL injection detected in password")
        
        return v
    
    @field_validator('ssh_key_path')
    @classmethod
    def validate_ssh_key_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        if not Validators.validate_file_path(v):
            raise ValueError("Invalid file path or potential path traversal attempt")
        
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        is_valid, sanitized = Validators.validate_description(v)
        if not is_valid:
            raise ValueError("Invalid description or potential injection attempt")
        
        return sanitized

class ServerCreate(ServerBase):
    pass

class ServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ssh_port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, max_length=1000)
    ssh_key_path: Optional[str] = Field(None, max_length=4096)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        is_valid, sanitized = Validators.validate_and_sanitize_name(v)
        if not is_valid:
            raise ValueError("Invalid name format or potential injection attempt")
        
        return sanitized
    
    @field_validator('hostname')
    @classmethod
    def validate_hostname(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        if not Validators.validate_hostname(v):
            raise ValueError("Invalid hostname or IP address format")
        
        if Validators.is_sql_injection_attempt(v):
            raise ValueError("Potential SQL injection detected in hostname")
        
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        if not Validators.validate_username(v):
            raise ValueError("Invalid username format")
        
        if Validators.is_sql_injection_attempt(v):
            raise ValueError("Potential SQL injection detected in username")
        
        return v

class ServerResponse(ServerBase):
    id: int
    last_check: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True