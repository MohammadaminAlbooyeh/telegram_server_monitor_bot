from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("backend")

class ErrorHandler:
    
    @staticmethod
    async def handle_exception(request: Request, exc: Exception):
        """Handle exceptions"""
        logger.error(f"Exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )