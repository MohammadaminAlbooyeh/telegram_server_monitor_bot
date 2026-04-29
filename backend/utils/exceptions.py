from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class APIException(Exception):
    """Base API exception"""
    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(self.message)

class ValidationError(APIException):
    """Data validation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")
        self.details = details or {}

class ServerNotFound(APIException):
    """Server not found"""
    def __init__(self, server_id: Optional[int] = None):
        msg = f"Server not found" if not server_id else f"Server with ID {server_id} not found"
        super().__init__(msg, status.HTTP_404_NOT_FOUND, "SERVER_NOT_FOUND")

class MetricNotFound(APIException):
    """Metric not found"""
    def __init__(self, server_id: Optional[int] = None):
        msg = f"No metrics found" if not server_id else f"No metrics found for server {server_id}"
        super().__init__(msg, status.HTTP_404_NOT_FOUND, "METRIC_NOT_FOUND")

class AlertNotFound(APIException):
    """Alert not found"""
    def __init__(self, alert_id: Optional[int] = None):
        msg = f"Alert not found" if not alert_id else f"Alert with ID {alert_id} not found"
        super().__init__(msg, status.HTTP_404_NOT_FOUND, "ALERT_NOT_FOUND")

class UserNotFound(APIException):
    """User not found"""
    def __init__(self, user_id: Optional[int] = None):
        msg = f"User not found" if not user_id else f"User with ID {user_id} not found"
        super().__init__(msg, status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND")

class UserNotAuthorized(APIException):
    """User not authorized"""
    def __init__(self, message: str = "User not authorized"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "UNAUTHORIZED")

class InvalidCredentials(APIException):
    """Invalid credentials"""
    def __init__(self):
        super().__init__("Invalid credentials", status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS")

class DuplicateResource(APIException):
    """Resource already exists"""
    def __init__(self, resource_type: str, field: str, value: str):
        msg = f"{resource_type} with {field}='{value}' already exists"
        super().__init__(msg, status.HTTP_409_CONFLICT, "DUPLICATE_RESOURCE")

class DatabaseError(APIException):
    """Database operation error"""
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, "DATABASE_ERROR")

class SSHConnectionError(APIException):
    """SSH connection error"""
    def __init__(self, hostname: str, message: Optional[str] = None):
        msg = f"Failed to connect to {hostname}" if not message else f"SSH error for {hostname}: {message}"
        super().__init__(msg, status.HTTP_503_SERVICE_UNAVAILABLE, "SSH_CONNECTION_ERROR")

class ExternalServiceError(APIException):
    """External service error (e.g., Telegram API)"""
    def __init__(self, service: str, message: Optional[str] = None):
        msg = f"{service} service error" if not message else f"{service} service error: {message}"
        super().__init__(msg, status.HTTP_502_BAD_GATEWAY, "EXTERNAL_SERVICE_ERROR")

class RateLimitExceeded(APIException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__("Rate limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after

def to_http_exception(exc: APIException) -> HTTPException:
    """Convert APIException to HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.error_code,
            "message": exc.message
        }
    )