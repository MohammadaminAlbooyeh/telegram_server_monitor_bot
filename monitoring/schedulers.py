import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.models.database import SessionLocal, Server, Metric, AlertConfig
from monitoring.collector import MetricsCollector
from monitoring.analyzer import MetricsAnalyzer
from monitoring.alerter import AlertManager
from config.settings import (
    METRICS_COLLECTION_INTERVAL,
    ALERT_CHECK_INTERVAL,
    METRICS_RETENTION_DAYS
)

logger = logging.getLogger("monitoring")

# Global scheduler instance
scheduler = None

def collect_metrics_job():
    """Background job to collect metrics from all active servers"""
    logger.info("Starting metrics collection job...")
    db = SessionLocal()
    
    try:
        servers = db.query(Server).filter(Server.is_active == True).all()
        
        if not servers:
            logger.info("No active servers to monitor")
            return
        
        logger.info(f"Collecting metrics from {len(servers)} servers...")
        
        for server in servers:
            try:
                collector = MetricsCollector({
                    'hostname': server.hostname,
                    'ssh_port': server.ssh_port,
                    'username': server.username,
                    'password': server.password,
                    'ssh_key_path': server.ssh_key_path
                })
                
                metrics = collector.collect_all_metrics()
                
                if metrics:
                    metric = Metric(
                        server_id=server.id,
                        timestamp=datetime.utcnow(),
                        **metrics
                    )
                    db.add(metric)
                    server.last_check = datetime.utcnow()
                    
                    logger.info(f"Metrics collected for {server.name}: CPU={metrics['cpu_usage']:.1f}%")
                else:
                    logger.warning(f"Failed to collect metrics for {server.name}")
                    server.is_active = False
            
            except Exception as e:
                logger.error(f"Error collecting metrics for {server.name}: {str(e)}")
        
        db.commit()
        logger.info("Metrics collection job completed")
    
    except Exception as e:
        logger.error(f"Metrics collection job failed: {str(e)}")
    
    finally:
        db.close()

def check_alerts_job():
    """Background job to check metrics against alert thresholds"""
    logger.info("Starting alert check job...")
    db = SessionLocal()
    
    try:
        servers = db.query(Server).filter(Server.is_active == True).all()
        
        for server in servers:
            try:
                latest_metric = db.query(Metric).filter(
                    Metric.server_id == server.id
                ).order_by(Metric.timestamp.desc()).first()
                
                if not latest_metric:
                    continue
                
                configs = db.query(AlertConfig).filter(
                    AlertConfig.server_id == server.id,
                    AlertConfig.enabled == True
                ).all()
                
                if not configs:
                    continue
                
                config_dicts = []
                for config in configs:
                    config_dicts.append({
                        'server_id': server.id,
                        'metric_type': config.metric_type.value,
                        'threshold_value': config.threshold_value,
                        'comparison_operator': config.comparison_operator,
                        'severity': config.severity.value,
                        'enabled': config.enabled
                    })
                
                metrics_dict = {
                    'cpu_usage': latest_metric.cpu_usage,
                    'memory_usage': latest_metric.memory_usage,
                    'disk_usage': latest_metric.disk_usage,
                    'network_in': latest_metric.network_in,
                    'network_out': latest_metric.network_out
                }
                
                triggered_alerts = MetricsAnalyzer.analyze_all_metrics(metrics_dict, config_dicts)
                
                for alert_data in triggered_alerts:
                    AlertManager.create_alert(
                        db=db,
                        server_id=server.id,
                        alert_type=alert_data['metric_type'],
                        severity=alert_data['severity'],
                        message=alert_data['message'],
                        value=alert_data['value'],
                        threshold=alert_data['threshold']
                    )
            
            except Exception as e:
                logger.error(f"Error checking alerts for {server.name}: {str(e)}")
        
        logger.info("Alert check job completed")
    
    except Exception as e:
        logger.error(f"Alert check job failed: {str(e)}")
    
    finally:
        db.close()

def cleanup_old_data_job():
    """Background job to clean up old metrics and alerts"""
    logger.info("Starting cleanup job...")
    db = SessionLocal()
    
    try:
        time_threshold = datetime.utcnow() - timedelta(days=METRICS_RETENTION_DAYS)
        
        deleted_metrics = db.query(Metric).filter(
            Metric.created_at < time_threshold
        ).delete()
        
        db.commit()
        
        logger.info(f"Deleted {deleted_metrics} old metrics")
    
    except Exception as e:
        logger.error(f"Cleanup job failed: {str(e)}")
    
    finally:
        db.close()

def start_scheduler():
    """Initialize and start the background scheduler"""
    global scheduler
    
    try:
        scheduler = BackgroundScheduler()
        
        scheduler.add_job(
            collect_metrics_job,
            trigger=IntervalTrigger(seconds=METRICS_COLLECTION_INTERVAL),
            id='collect_metrics',
            name='Collect metrics from servers',
            replace_existing=True
        )
        
        scheduler.add_job(
            check_alerts_job,
            trigger=IntervalTrigger(seconds=ALERT_CHECK_INTERVAL),
            id='check_alerts',
            name='Check metrics against alert thresholds',
            replace_existing=True
        )
        
        scheduler.add_job(
            cleanup_old_data_job,
            trigger=IntervalTrigger(hours=24),
            id='cleanup_old_data',
            name='Cleanup old metrics and alerts',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Background scheduler started")
    
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    try:
        if scheduler:
            scheduler.shutdown()
            logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")