"""Tests for NotificationService"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.notification_service import NotificationService


class TestNotificationService:
    """Test notification service"""
    
    @pytest.mark.asyncio
    async def test_send_telegram_message_success(self):
        """Test successful Telegram message send"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await NotificationService._send_telegram_message(
                chat_id=123456789,
                message="Test message"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_send_telegram_message_failure(self):
        """Test failed Telegram message send"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_post.return_value = mock_response
            
            result = await NotificationService._send_telegram_message(
                chat_id=123456789,
                message="Test message"
            )
            
            assert result is False
    
    def test_format_alert_message(self):
        """Test alert message formatting"""
        alert = MagicMock()
        alert.severity = "CRITICAL"
        alert.alert_type = "CPU"
        alert.message = "CPU usage high"
        alert.value = 95.5
        alert.threshold = 80.0
        alert.created_at = MagicMock()
        alert.created_at.strftime.return_value = "2024-01-01 12:00:00"
        alert.id = 1
        
        message = NotificationService._format_alert_message(alert, "test-server")
        
        assert "CRITICAL" in message
        assert "test-server" in message
        assert "CPU" in message
        assert "95.5" in message
        assert "80.0" in message
    
    @pytest.mark.asyncio
    async def test_notify_user(self):
        """Test notifying a single user"""
        with patch.object(NotificationService, '_send_telegram_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await NotificationService.notify_user(
                user_id=1,
                message="Test notification",
                telegram_id=123456789
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_test_message(self):
        """Test sending test message"""
        with patch.object(NotificationService, '_send_telegram_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await NotificationService.send_test_message(123456789)
            
            assert result is True
            mock_send.assert_called_once()
