from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import signal
import asyncio

from config.settings import CORS_ORIGINS, DEBUG, API_HOST, API_PORT
from backend.models.database import init_db
from backend.api.routes import servers, metrics, alerts, users, health, auth, export, bots
from backend.middleware.rate_limit import (
    RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
)

logger = logging.getLogger("backend")

# Initialize FastAPI
app = FastAPI(
    title="Server Monitoring Bot API",
    description="FastAPI backend for Telegram server monitoring bot",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add middleware (order matters - add security/logging first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Graceful shutdown handler
shutdown_signal_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.warning(f"Received signal {signum}. Starting graceful shutdown...")
    shutdown_signal_event.set()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    try:
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize scheduler
        logger.info("Initializing background scheduler...")
        try:
            from monitoring.schedulers import start_scheduler
            start_scheduler()
            logger.info("Background scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_app():
    """Graceful shutdown event"""
    logger.info("Shutting down application...")
    try:
        # Stop scheduler
        logger.info("Stopping background scheduler...")
        try:
            from monitoring.schedulers import scheduler
            if scheduler and scheduler.running:
                scheduler.shutdown(wait=True)
                logger.info("Background scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {str(e)}")
        
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Include routers
app.include_router(servers.router, prefix="/api", tags=["servers"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(bots.router, prefix="/api", tags=["bots"])

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Server Monitoring Bot API",
        "version": "1.0.0",
        "docs_url": "/api/docs",
        "redoc_url": "/api/redoc",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    
    log_level = "debug" if DEBUG else "info"
    
    # Run with SSL if configured
    ssl_keyfile = None
    ssl_certfile = None
    
    try:
        from config.settings import SSL_ENABLED
        if SSL_ENABLED:
            ssl_keyfile = "/app/certs/key.pem"
            ssl_certfile = "/app/certs/cert.pem"
            logger.info("SSL enabled for API server")
    except Exception:
        pass
    
    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        log_level=log_level,
        reload=DEBUG,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        workers=1 if DEBUG else 4
    )