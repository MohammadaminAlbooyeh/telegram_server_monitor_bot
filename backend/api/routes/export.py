"""
Export routes for metrics and alerts

Provides endpoints to export data in CSV and JSON formats
"""

from fastapi import APIRouter, Depends, HTTPException, status  # noqa: F401
from fastapi.responses import StreamingResponse
import csv
import json
import io
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db, get_current_user
from backend.models.metric import Metric
from backend.models.alert import Alert
from backend.models.user import User

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/metrics/csv")
async def export_metrics_csv(
    server_id: int = None,
    days: int = 7,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export metrics to CSV format
    
    Args:
        server_id: Optional server ID to filter metrics
        days: Number of days to export (default: 7)
        
    Returns:
        CSV file download
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query metrics
        query = db.query(Metric).filter(
            Metric.timestamp >= start_date,
            Metric.timestamp <= end_date
        )
        
        if server_id:
            query = query.filter(Metric.server_id == server_id)
        
        metrics = query.order_by(Metric.timestamp).all()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No metrics found for the specified criteria"
            )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Server ID", "Server Name", "CPU Usage (%)", "Memory Usage (%)",
            "Disk Usage (%)", "Network Latency (ms)", "Uptime (s)", "Timestamp"
        ])
        
        # Write data
        for metric in metrics:
            writer.writerow([
                metric.server_id,
                metric.server.name if metric.server else "Unknown",
                metric.cpu_usage,
                metric.memory_usage,
                metric.disk_usage,
                metric.network_latency,
                metric.uptime,
                metric.timestamp.isoformat()
            ])
        
        # Prepare response
        output.seek(0)
        filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export metrics: {str(e)}"
        ) from e


@router.get("/metrics/json")
async def export_metrics_json(
    server_id: int = None,
    days: int = 7,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export metrics to JSON format
    
    Args:
        server_id: Optional server ID to filter metrics
        days: Number of days to export (default: 7)
        
    Returns:
        JSON file download
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query metrics
        query = db.query(Metric).filter(
            Metric.timestamp >= start_date,
            Metric.timestamp <= end_date
        )
        
        if server_id:
            query = query.filter(Metric.server_id == server_id)
        
        metrics = query.order_by(Metric.timestamp).all()
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No metrics found for the specified criteria"
            )
        
        # Create JSON
        data = {
            "exported_at": datetime.now().isoformat(),
            "filter": {
                "server_id": server_id,
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": [
                {
                    "server_id": metric.server_id,
                    "server_name": metric.server.name if metric.server else "Unknown",
                    "cpu_usage": metric.cpu_usage,
                    "memory_usage": metric.memory_usage,
                    "disk_usage": metric.disk_usage,
                    "network_latency": metric.network_latency,
                    "uptime": metric.uptime,
                    "timestamp": metric.timestamp.isoformat()
                }
                for metric in metrics
            ]
        }
        
        # Prepare response
        output = io.StringIO()
        json.dump(data, output, indent=2)
        output.seek(0)
        filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export metrics: {str(e)}"
        ) from e


@router.get("/alerts/csv")
async def export_alerts_csv(
    server_id: int = None,
    status_filter: str = None,
    days: int = 7,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export alerts to CSV format
    
    Args:
        server_id: Optional server ID to filter alerts
        status_filter: Alert status to filter (is_resolved, is_acknowledged)
        days: Number of days to export (default: 7)
        
    Returns:
        CSV file download
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query alerts
        query = db.query(Alert).filter(
            Alert.created_at >= start_date,
            Alert.created_at <= end_date
        )
        
        if server_id:
            query = query.filter(Alert.server_id == server_id)
        
        if status_filter == "resolved":
            query = query.filter(Alert.is_resolved is True)
        elif status_filter == "acknowledged":
            query = query.filter(Alert.is_acknowledged is True)
        
        alerts = query.order_by(Alert.created_at.desc()).all()
        
        if not alerts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No alerts found for the specified criteria"
            )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Alert ID", "Server ID", "Server Name", "Alert Type", "Message",
            "Severity", "Value", "Threshold", "Is Acknowledged", "Is Resolved",
            "Created At", "Resolved At"
        ])
        
        # Write data
        for alert in alerts:
            writer.writerow([
                alert.id,
                alert.server_id,
                alert.server.name if alert.server else "Unknown",
                alert.alert_type.value,
                alert.message,
                alert.severity.value,
                alert.value,
                alert.threshold,
                alert.is_acknowledged,
                alert.is_resolved,
                alert.created_at.isoformat(),
                alert.resolved_at.isoformat() if alert.resolved_at else ""
            ])
        
        # Prepare response
        output.seek(0)
        filename = f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export alerts: {str(e)}"
        ) from e


@router.get("/alerts/json")
async def export_alerts_json(
    server_id: int = None,
    status_filter: str = None,
    days: int = 7,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export alerts to JSON format
    
    Args:
        server_id: Optional server ID to filter alerts
        status_filter: Alert status to filter (is_resolved, is_acknowledged)
        days: Number of days to export (default: 7)
        
    Returns:
        JSON file download
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query alerts
        query = db.query(Alert).filter(
            Alert.created_at >= start_date,
            Alert.created_at <= end_date
        )
        
        if server_id:
            query = query.filter(Alert.server_id == server_id)
        
        if status_filter == "resolved":
            query = query.filter(Alert.is_resolved is True)
        elif status_filter == "acknowledged":
            query = query.filter(Alert.is_acknowledged is True)
        
        alerts = query.order_by(Alert.created_at.desc()).all()
        
        if not alerts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No alerts found for the specified criteria"
            )
        
        # Create JSON
        data = {
            "exported_at": datetime.now().isoformat(),
            "filter": {
                "server_id": server_id,
                "status": status_filter,
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "alerts": [
                {
                    "id": alert.id,
                    "server_id": alert.server_id,
                    "server_name": alert.server.name if alert.server else "Unknown",
                    "alert_type": alert.alert_type.value,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "is_acknowledged": alert.is_acknowledged,
                    "is_resolved": alert.is_resolved,
                    "created_at": alert.created_at.isoformat(),
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in alerts
            ]
        }
        
        # Prepare response
        output = io.StringIO()
        json.dump(data, output, indent=2)
        output.seek(0)
        filename = f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export alerts: {str(e)}"
        ) from e
