from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from backend.models.alert import Alert
from backend.schemas.alert import AlertCreate, AlertUpdate

logger = logging.getLogger("backend")

class AlertService:
    
    @staticmethod
    def create_alert(db: Session, alert: AlertCreate) -> Alert:
        """Create new alert"""
        db_alert = Alert(**alert.dict())
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert
    
    @staticmethod
    def get_alert(db: Session, alert_id: int) -> Alert:
        """Get alert by ID"""
        return db.query(Alert).filter(Alert.id == alert_id).first()
    
    @staticmethod
    def list_alerts(db: Session, skip: int = 0, limit: int = 50) -> list:
        """List alerts"""
        return db.query(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_alert(db: Session, alert_id: int, alert_update: AlertUpdate) -> Alert:
        """Update alert"""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            if alert_update.is_acknowledged:
                alert.is_acknowledged = True
                alert.acknowledged_at = datetime.utcnow()
            if alert_update.is_resolved:
                alert.is_resolved = True
                alert.resolved_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        return alert
    
    @staticmethod
    def delete_alert(db: Session, alert_id: int) -> bool:
        """Delete alert"""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            db.delete(alert)
            db.commit()
            return True
        return False