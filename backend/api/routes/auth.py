from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from backend.models.database import get_db

logger = logging.getLogger("backend")
router = APIRouter()

@router.post("/auth/login")
async def login(db: Session = Depends(get_db)):
    """Login endpoint"""
    return {"message": "Login endpoint"}

@router.post("/auth/verify")
async def verify(db: Session = Depends(get_db)):
    """Verify token"""
    return {"message": "Verify endpoint"}

@router.post("/auth/refresh")
async def refresh(db: Session = Depends(get_db)):
    """Refresh token"""
    return {"message": "Refresh endpoint"}