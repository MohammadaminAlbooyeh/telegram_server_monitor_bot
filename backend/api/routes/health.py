from datetime import datetime
import logging
import psutil
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models.database import get_db, Server, Metric, Alert
from config.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger("backend")
router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check overall system health"""
    health_status = {"status": "healthy", "checks": {}}
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Telegram bot token
    if TELEGRAM_BOT_TOKEN:
        health_status["checks"]["telegram"] = {
            "status": "configured",
            "message": "Telegram bot token configured"
        }
    else:
        health_status["checks"]["telegram"] = {
            "status": "warning",
            "message": "Telegram bot token not configured"
        }
    
    return health_status


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed system health with metrics"""
    try:
        # Database stats
        server_count = db.query(Server).count()
        active_servers = db.query(Server).filter(Server.is_active == True).count()
        metric_count = db.query(Metric).count()
        alert_count = db.query(Alert).count()
        unresolved_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
        
        # System stats
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "system": {
                "cpu_percent": cpu_usage,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_available_gb": disk.free / (1024 * 1024 * 1024)
            },
            "database": {
                "total_servers": server_count,
                "active_servers": active_servers,
                "inactive_servers": server_count - active_servers,
                "total_metrics": metric_count,
                "total_alerts": alert_count,
                "unresolved_alerts": unresolved_alerts
            },
            "status_details": {
                "database": "healthy" if server_count >= 0 else "unhealthy",
                "storage": "healthy" if disk.percent < 90 else "warning",
                "memory": "healthy" if memory.percent < 85 else "warning",
                "cpu": "healthy" if cpu_usage < 80 else "warning"
            }
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get detailed health status")


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness check"""
    try:
        # Check if database is accessible
        db.execute(text("SELECT 1"))
        
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "NOT_READY", "message": str(e)}
        )


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness check"""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/scheduler")
async def scheduler_health_check(db: Session = Depends(get_db)):
    """Check background scheduler health"""
    try:
        from monitoring.schedulers import scheduler
        
        if scheduler is None:
            return {
                "status": "stopped",
                "message": "Scheduler not started",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not scheduler.running:
            return {
                "status": "stopped",
                "message": "Scheduler is not running",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get scheduler job status
        jobs = scheduler.get_jobs()
        job_details = [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ]
        
        return {
            "status": "running",
            "message": f"Scheduler is running with {len(jobs)} jobs",
            "jobs": job_details,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Scheduler health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "SCHEDULER_ERROR", "message": str(e)}
        )
