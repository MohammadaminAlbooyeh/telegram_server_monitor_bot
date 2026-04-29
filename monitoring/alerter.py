import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, List

logger = logging.getLogger("monitoring")

class AlertManager:
    """Manage alert creation and state"""
    
    @staticmethod
    def should_create_alert(
        db: Session,
        server_id: int,
        alert_type: str,
        recent_hours: int = 1
    ) -> bool:
        """Check if we should create alert (avoid duplicates)"""
        from backend.models.alert import Alert
        
        time_threshold = datetime.utcnow() - timedelta(hours=recent_hours)
        
        existing_alert = db.query(Alert).filter(
            Alert.server_id == server_id,
            Alert.alert_type == alert_type,
            Alert.is_resolved == False,
            Alert.created_at >= time_threshold
        ).first()
        
        return existing_alert is None
    
    @staticmethod
    def create_alert(
        db: Session,
        server_id: int,
        alert_type: str,
        severity: str,
        message: str,
        value: float,
        threshold: float
    ) -> Optional[int]:
        """Create new alert in database"""
        from backend.models.alert import Alert
        
        if not AlertManager.should_create_alert(db, server_id, alert_type):
            logger.info(f"Skipping duplicate alert for server {server_id}, type {alert_type}")
            return None
        
        try:
            alert = Alert(
                server_id=server_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                value=value,
                threshold=threshold,
                is_acknowledged=False,
                is_resolved=False,
                created_at=datetime.utcnow()
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.warning(f"Alert created: {alert_type} for server {server_id} - {message}")
            return alert.id
        
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int) -> bool:
        """Mark alert as acknowledged"""
        from backend.models.alert import Alert
        
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {str(e)}")
            return False
    
    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> bool:
        """Mark alert as resolved"""
        from backend.models.alert import Alert
        
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Alert {alert_id} resolved")
            return True
        
        except Exception as e:
            logger.error(f"Failed to resolve alert: {str(e)}")
            return False