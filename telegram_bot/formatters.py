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
    def format_bots_status(bots_status: dict) -> str:
        """Format runtime status for multiple bots."""
        if not bots_status:
            return "No bot status available"

        bots = bots_status.get("multi_bots", {})
        stale_after = bots_status.get("stale_after_seconds", 0)
        up_count = bots_status.get("up_count", 0)
        down_count = bots_status.get("down_count", 0)

        message = f"🤖 *Bot Status*\n\n"
        message += f"Up: `{up_count}`  Down: `{down_count}`\n"
        message += f"Stale after: `{stale_after}s`\n\n"

        for bot_name, bot in bots.items():
            state_icon = "🟢" if bot.get("is_up") else "🔴"
            state_text = "UP" if bot.get("is_up") else "DOWN"
            heartbeat_age = bot.get("heartbeat_age_seconds")
            heartbeat_text = "n/a" if heartbeat_age is None else f"{heartbeat_age:.0f}s ago"
            error = bot.get("error")

            message += f"{state_icon} *{bot_name}* - `{state_text}`\n"
            message += f"Configured: `{'yes' if bot.get('configured') else 'no'}`\n"
            message += f"Last heartbeat: `{heartbeat_text}`\n"
            if error:
                message += f"Error: `{error}`\n"
            message += "\n"

        return message.strip()
    
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
