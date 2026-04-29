from sqlalchemy.orm import Session
import logging

from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger("backend")

class UserService:
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create new user"""
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> User:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: str) -> User:
        """Get user by Telegram ID"""
        return db.query(User).filter(User.telegram_user_id == telegram_id).first()
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list:
        """List all users"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            update_data = user_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user