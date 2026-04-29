import logging
import httpx
from typing import List, Optional, Dict
from datetime import datetime
from config.settings import TELEGRAM_BOT_TOKEN, BACKEND_URL

logger = logging.getLogger("backend")

class NotificationService:
    TELEGRAM_API_URL = "https://api.telegram.org"
    
    @staticmethod
    async def _send_telegram_message(chat_id: int, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram chat"""
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not configured")
            return False
        
        url = f"{NotificationService.TELEGRAM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Message sent to chat {chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send message to {chat_id}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    @staticmethod
    def _format_alert_message(alert, server_name: str) -> str:
        """Format alert message for Telegram"""
        severity_emoji = {
            "CRITICAL": "🔴",
            "WARNING": "🟠",
            "INFO": "🔵"
        }
        
        emoji = severity_emoji.get(alert.severity, "⚠️")
        
        message = f"""
{emoji} <b>Alert: {alert.severity}</b>

<b>Server:</b> {server_name}
<b>Type:</b> {alert.alert_type}
<b>Message:</b> {alert.message}

<b>Current Value:</b> {alert.value:.2f}%
<b>Threshold:</b> {alert.threshold:.2f}%
<b>Time:</b> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

<a href="{BACKEND_URL}/api/alerts/{alert.id}">View in Dashboard</a>
"""
        return message.strip()
    
    @staticmethod
    async def send_alert_to_telegram(alert, users: List) -> Dict[int, bool]:
        """Send alert to Telegram users"""
        if not users:
            logger.warning(f"No users to notify for alert {alert.id}")
            return {}
        
        results = {}
        
        try:
            # Get server name
            from backend.models.database import SessionLocal, Server
            db = SessionLocal()
            server = db.query(Server).filter(Server.id == alert.server_id).first()
            server_name = server.name if server else f"Server {alert.server_id}"
            db.close()
            
            message = NotificationService._format_alert_message(alert, server_name)
            
            for user in users:
                chat_id = user.telegram_id if hasattr(user, 'telegram_id') else user.get('telegram_id')
                if not chat_id:
                    logger.warning(f"User {user} has no telegram_id")
                    results[chat_id] = False
                    continue
                
                success = await NotificationService._send_telegram_message(chat_id, message)
                results[chat_id] = success
                logger.info(f"Alert notification sent to user {chat_id}: {'Success' if success else 'Failed'}")
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {str(e)}")
            return {}
    
    @staticmethod
    async def notify_user(user_id: int, message: str, telegram_id: Optional[int] = None) -> bool:
        """Notify single user with custom message"""
        if not telegram_id:
            try:
                from backend.models.database import SessionLocal, User
                db = SessionLocal()
                user = db.query(User).filter(User.id == user_id).first()
                telegram_id = user.telegram_id if user else None
                db.close()
            except Exception as e:
                logger.error(f"Failed to get user {user_id}: {str(e)}")
                return False
        
        if not telegram_id:
            logger.error(f"No telegram_id found for user {user_id}")
            return False
        
        return await NotificationService._send_telegram_message(telegram_id, message)
    
    @staticmethod
    async def broadcast_alert(alert, exclude_user_ids: Optional[List[int]] = None) -> Dict[int, bool]:
        """Broadcast alert to all active users"""
        try:
            from backend.models.database import SessionLocal, User
            db = SessionLocal()
            
            # Get all active users with telegram_id
            query = db.query(User).filter(User.is_active == True)
            if exclude_user_ids:
                query = query.filter(~User.id.in_(exclude_user_ids))
            
            users = query.all()
            db.close()
            
            if not users:
                logger.info("No active users to broadcast alert")
                return {}
            
            logger.info(f"Broadcasting alert to {len(users)} users")
            return await NotificationService.send_alert_to_telegram(alert, users)
        
        except Exception as e:
            logger.error(f"Failed to broadcast alert: {str(e)}")
            return {}
    
    @staticmethod
    async def send_status_update(telegram_id: int, status_data: Dict) -> bool:
        """Send status update to user"""
        try:
            message = f"""
<b>Server Status Update</b>

<b>Total Servers:</b> {status_data.get('total_servers', 0)}
<b>Active Servers:</b> {status_data.get('active_servers', 0)}
<b>Inactive Servers:</b> {status_data.get('inactive_servers', 0)}

<b>Pending Alerts:</b> {status_data.get('pending_alerts', 0)}
<b>Critical Alerts:</b> {status_data.get('critical_alerts', 0)}
<b>Warning Alerts:</b> {status_data.get('warning_alerts', 0)}

<b>Last Update:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
            return await NotificationService._send_telegram_message(telegram_id, message.strip())
        except Exception as e:
            logger.error(f"Failed to send status update: {str(e)}")
            return False
    
    @staticmethod
    async def send_test_message(telegram_id: int) -> bool:
        """Send test message to verify Telegram connection"""
        message = "✅ <b>Test Message</b>\n\nTelegram notifications are working correctly!"
        return await NotificationService._send_telegram_message(telegram_id, message)