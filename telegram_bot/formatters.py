import logging

logger = logging.getLogger("telegram_bot")

class BotFormatters:
    """Format API responses for Telegram messages"""
    
    @staticmethod
    def format_metric(metric: dict) -> str:
        """Format metric data for display"""
        if not metric:
            return "No metrics available"
        
        return (
            f"📊 *Server Metrics*\n\n"
            f"🔴 CPU: `{metric.get('cpu_usage', 0):.1f}%`\n"
            f"🟡 Memory: `{metric.get('memory_usage', 0):.1f}%`\n"
            f"🟢 Disk: `{metric.get('disk_usage', 0):.1f}%`\n"
            f"📡 Load: `{metric.get('load_average_1', 0):.2f}`"
        )
    
    @staticmethod
    def format_server_status(server: dict, metric: dict = None) -> str:
        """Format server status for display"""
        status_icon = "🟢" if metric else "🔴"
        
        message = f"{status_icon} *{server['name']}*\n"
        message += f"Host: `{server['hostname']}`\n"
        message += f"Port: `{server['ssh_port']}`\n"
        
        return message
    
    @staticmethod
    def format_alerts(alerts: list) -> str:
        """Format alerts for display"""
        if not alerts:
            return "✅ No active alerts"
        
        message = f"⚠️ *Recent Alerts ({len(alerts)})*\n\n"
        
        for alert in alerts[:5]:
            severity_icon = {
                'CRITICAL': '🔴',
                'WARNING': '🟡',
                'INFO': '🔵'
            }.get(alert.get('severity', 'INFO'), '⚪')
            
            message += f"{severity_icon} {alert.get('alert_type')}\n"
            message += f"Value: `{alert.get('value', 0):.1f}%`\n\n"
        
        return message