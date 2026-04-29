from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    telegram_user_id: str
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    telegram_username: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    notification_enabled: Optional[bool] = None
    notification_quiet_start: Optional[int] = None
    notification_quiet_end: Optional[int] = None

class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    notification_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True