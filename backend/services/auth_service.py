import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("backend")

class AuthService:
    
    @staticmethod
    def generate_api_key(user_id: int) -> str:
        """Generate API key"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key"""
        if not api_key:
            return False
        return True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """Verify password"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hash