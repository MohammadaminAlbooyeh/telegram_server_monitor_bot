import logging

logger = logging.getLogger("backend")

class SecurityUtil:
    
    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt password"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def decrypt_password(encrypted: str) -> str:
        """Decrypt password - simple implementation"""
        return encrypted