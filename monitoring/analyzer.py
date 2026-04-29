import logging
from typing import Dict, List, Optional

logger = logging.getLogger("monitoring")

class MetricsAnalyzer:
    """Analyze metrics and compare against thresholds"""
    
    @staticmethod
    def check_threshold(value: float, threshold: float, operator: str) -> bool:
        """Check if value exceeds threshold"""
        if operator == '>':
            return value > threshold
        elif operator == '<':
            return value < threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return value == threshold
        return False
    
    @staticmethod
    def determine_severity(value: float, threshold: float, metric_type: str) -> str:
        """Determine alert severity"""
        if value >= threshold * 1.5:
            return "CRITICAL"
        elif value >= threshold * 1.1:
            return "WARNING"
        else:
            return "INFO"
    
    @staticmethod
    def analyze_metric(metric_value: float, config: Dict) -> Optional[Dict]:
        """Analyze single metric against configuration"""
        threshold_value = config.get('threshold_value')
        operator = config.get('comparison_operator')
        metric_type = config.get('metric_type')
        
        if not MetricsAnalyzer.check_threshold(metric_value, threshold_value, operator):
            return None
        
        severity = MetricsAnalyzer.determine_severity(metric_value, threshold_value, metric_type)
        
        return {
            'metric_type': metric_type,
            'value': metric_value,
            'threshold': threshold_value,
            'severity': severity,
            'message': f"{metric_type} usage at {metric_value:.1f}% (threshold: {threshold_value}%)"
        }
    
    @staticmethod
    def analyze_all_metrics(metrics: Dict, configs: List[Dict]) -> List[Dict]:
        """Analyze all metrics and return list of alerts"""
        alerts = []
        
        metric_mapping = {
            'CPU': metrics.get('cpu_usage', 0),
            'MEMORY': metrics.get('memory_usage', 0),
            'DISK': metrics.get('disk_usage', 0),
            'NETWORK': metrics.get('network_in', 0) + metrics.get('network_out', 0),
        }
        
        for config in configs:
            if not config.get('enabled'):
                continue
            
            metric_type = config.get('metric_type')
            metric_value = metric_mapping.get(metric_type, 0)
            
            alert = MetricsAnalyzer.analyze_metric(metric_value, config)
            if alert:
                alert['server_id'] = config.get('server_id')
                alerts.append(alert)
        
        return alerts