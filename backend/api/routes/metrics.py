from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from backend.models.database import get_db, Server, Metric
from backend.schemas.metric import MetricCreate, MetricResponse

logger = logging.getLogger("backend")
router = APIRouter()

@router.get("/metrics/{server_id}", response_model=list[MetricResponse])
async def get_metrics(
    server_id: int,
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get metrics history for server"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    metrics = db.query(Metric).filter(
        Metric.server_id == server_id,
        Metric.timestamp >= start_time
    ).order_by(Metric.timestamp.desc()).limit(limit).all()
    
    return metrics

@router.get("/metrics/{server_id}/current", response_model=MetricResponse)
async def get_current_metrics(
    server_id: int,
    db: Session = Depends(get_db)
):
    """Get latest metrics for server"""
    metric = db.query(Metric).filter(
        Metric.server_id == server_id
    ).order_by(Metric.timestamp.desc()).first()
    
    if not metric:
        raise HTTPException(status_code=404, detail="No metrics found")
    
    return metric

@router.post("/metrics", response_model=MetricResponse, status_code=201)
async def create_metric(
    metric: MetricCreate,
    db: Session = Depends(get_db)
):
    """Create new metric"""
    server = db.query(Server).filter(Server.id == metric.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    db_metric = Metric(**metric.dict())
    db.add(db_metric)
    
    server.last_check = datetime.utcnow()
    
    db.commit()
    db.refresh(db_metric)
    
    return db_metric