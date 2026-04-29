from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.models.database import get_db

async def verify_api_key(api_key: str):
    """Verify API key"""
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    return api_key

async def get_current_user(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """Get current user"""
    return {"api_key": api_key}