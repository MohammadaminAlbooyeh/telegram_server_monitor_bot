from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import Optional

from backend.models.database import get_db, Alert, Server
from backend.schemas.alert import AlertCreate, AlertResponse, AlertUpdate, AlertSeverityEnum
from backend.utils.exceptions import (
    AlertNotFound, ServerNotFound, DatabaseError, to_http_exception
)

logger = logging.getLogger("backend")
router = APIRouter()

@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    server_id: Optional[int] = Query(None, ge=1),
    is_acknowledged: Optional[bool] = None,
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get alerts with optional filters"""
    try:
        query = db.query(Alert)
        
        if server_id:
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise ServerNotFound(server_id)
            query = query.filter(Alert.server_id == server_id)
        
        if is_acknowledged is not None:
            query = query.filter(Alert.is_acknowledged == is_acknowledged)
        
        if is_resolved is not None:
            query = query.filter(Alert.is_resolved == is_resolved)
        
        if severity:
            try:
                AlertSeverityEnum(severity)  # Validate severity
                query = query.filter(Alert.severity == severity)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail={"error": "VALIDATION_ERROR", "message": f"Invalid severity: {severity}"}
                )
        
        alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
        return alerts
    
    except ServerNotFound as e:
        raise to_http_exception(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing alerts: {str(e)}")
        raise to_http_exception(DatabaseError("Failed to retrieve alerts"))

@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get single alert by ID"""
    try:
        if alert_id <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": "VALIDATION_ERROR", "message": "Alert ID must be positive"}
            )
        
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise AlertNotFound(alert_id)
        
        return alert
    
    except AlertNotFound as e:
        raise to_http_exception(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {str(e)}")
        raise to_http_exception(DatabaseError("Failed to retrieve alert"))

@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create new alert"""
    try:
        # Verify server exists
        server = db.query(Server).filter(Server.id == alert.server_id).first()
        if not server:
            raise ServerNotFound(alert.server_id)
        
        db_alert = Alert(**alert.dict())
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        logger.warning(f"Alert created: {alert.alert_type} for server {alert.server_id}")
        return db_alert
    
    except ServerNotFound as e:
        db.rollback()
        raise to_http_exception(e)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating alert: {str(e)}")
        raise to_http_exception(DatabaseError("Failed to create alert"))

@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update alert"""
    try:
        if alert_id <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": "VALIDATION_ERROR", "message": "Alert ID must be positive"}
            )
        
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise AlertNotFound(alert_id)
        
        update_data = alert_update.dict(exclude_unset=True)
        
        if "is_acknowledged" in update_data:
            alert.is_acknowledged = update_data["is_acknowledged"]
            alert.acknowledged_at = datetime.utcnow() if update_data["is_acknowledged"] else None

        if "is_resolved" in update_data:
            alert.is_resolved = update_data["is_resolved"]
            alert.resolved_at = datetime.utcnow() if update_data["is_resolved"] else None
        
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert updated: {alert_id}")
        return alert
    
    except AlertNotFound as e:
        db.rollback()
        raise to_http_exception(e)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        raise to_http_exception(DatabaseError("Failed to update alert"))

@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete alert"""
    try:
        if alert_id <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": "VALIDATION_ERROR", "message": "Alert ID must be positive"}
            )
        
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise AlertNotFound(alert_id)
        
        db.delete(alert)
        db.commit()
        
        logger.info(f"Alert deleted: {alert_id}")
        return None
    
    except AlertNotFound as e:
        raise to_http_exception(e)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting alert {alert_id}: {str(e)}")
        raise to_http_exception(DatabaseError("Failed to delete alert"))
