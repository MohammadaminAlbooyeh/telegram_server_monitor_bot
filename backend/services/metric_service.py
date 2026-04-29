from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from backend.models.metric import Metric
from backend.schemas.metric import MetricCreate

logger = logging.getLogger("backend")

class MetricService:
    
    @staticmethod
    def create_metric(db: Session, metric: MetricCreate) -> Metric:
        """Create new metric"""
        db_metric = Metric(**metric.dict())
        db.add(db_metric)
        db.commit()
        db.refresh(db_metric)
        return db_metric
    
    @staticmethod
    def get_latest_metric(db: Session, server_id: int) -> Metric:
        """Get latest metric for server"""
        return db.query(Metric).filter(
            Metric.server_id == server_id
        ).order_by(Metric.timestamp.desc()).first()
    
    @staticmethod
    def get_metrics_history(db: Session, server_id: int, hours: int = 24) -> list:
        """Get metrics history"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return db.query(Metric).filter(
            Metric.server_id == server_id,
            Metric.timestamp >= start_time
        ).order_by(Metric.timestamp.desc()).all()
    
    @staticmethod
    def cleanup_old_metrics(db: Session, days: int = 30) -> int:
        """Delete old metrics"""
        time_threshold = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(Metric).filter(
            Metric.created_at < time_threshold
        ).delete()
        db.commit()
        return deleted_count