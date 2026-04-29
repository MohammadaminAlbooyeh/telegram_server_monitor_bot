from fastapi import Request, HTTPException
import logging

logger = logging.getLogger("backend")

class AuthMiddleware:
    
    @staticmethod
    async def verify_api_key(request: Request):
        """Verify API key"""
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
        return api_key