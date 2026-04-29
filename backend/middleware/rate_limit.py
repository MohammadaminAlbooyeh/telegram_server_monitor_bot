import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

logger = logging.getLogger("backend")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory token bucket"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Check rate limit
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self.request_times[client_ip] = [
            req_time for req_time in self.request_times[client_ip]
            if req_time > one_minute_ago
        ]
        
        # Check if limit exceeded
        if len(self.request_times[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.request_times[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.request_times[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request/response logging"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for health checks to reduce noise
        if request.url.path == "/api/health":
            return await call_next(request)
        
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Client: {client_ip}"
        )
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] Response: {response.status_code} - Duration: {duration:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] Error after {duration:.3f}s: {str(exc)}",
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
