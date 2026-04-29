import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import ALLOWED_USERS
from telegram_bot.formatters import BotFormatters

logger = logging.getLogger("telegram_bot")

class CommandHandlers:
    """Handle bot commands"""
    
    def __init__(self, api_client, bot_name: str = None):
        self.api_client = api_client
        self.bot_name = bot_name or "telegram_bot"
        self.formatters = BotFormatters()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if user.id not in ALLOWED_USERS:
            logger.warning(f"Unauthorized user started bot {self.bot_name}: {user.id}")
        
        # Register user
        await self.api_client.create_user(
            telegram_user_id=str(user.id),
            telegram_username=user.username,
            telegram_first_name=user.first_name
        )
        
        logger.info(f"User {user.id} started bot {self.bot_name}")
        
        welcome_text = (
            f"👋 *Welcome, {user.first_name}!*\n\n"
            f"I'm your server monitoring bot.\n\n"
            f"Use /help to see available commands."
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Status", callback_data="status")],
            [InlineKeyboardButton("📈 Metrics", callback_data="metrics")],
            [InlineKeyboardButton("⚠️ Alerts", callback_data="alerts")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ])
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)
        logger.info(f"User started bot: {user.id}")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        
        if user.id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        await update.message.reply_text("🔄 Loading server status...")

        try:
            servers = await self.api_client.get_servers()
            if not servers:
                await update.message.reply_text("⚠️ No servers found or backend is unreachable.")
                return

            message = "*Server Status*\n\n"
            for server in servers:
                metric = await self.api_client.get_metrics(server['id'])
                message += self.formatters.format_server_status(server, metric)
                message += "\n\n"

            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error("Failed to build /status response for %s: %s", self.bot_name, str(e))
            await update.message.reply_text("❌ Error loading status. Please try again.")
    
    async def metrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /metrics command"""
        user = update.effective_user
        
        if user.id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        servers = await self.api_client.get_servers()
        
        if not servers:
            await update.message.reply_text("❌ No servers configured")
            return
        
        keyboard = []
        for server in servers:
            keyboard.append([
                InlineKeyboardButton(
                    f"📊 {server['name']}",
                    callback_data=f"metrics_{server['id']}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📊 *Select server for metrics:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        user = update.effective_user
        
        if user.id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        await update.message.reply_text("🔄 Loading alerts...")
        
        alerts = await self.api_client.get_alerts(is_acknowledged=False)
        message = self.formatters.format_alerts(alerts)
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "*Available Commands*\n\n"
            "🚀 *General*\n"
            "/start - Initialize bot\n"
            "/help - Show this help message\n\n"
            "📊 *Monitoring*\n"
            "/status - Show all servers status\n"
            "/metrics - View server metrics\n"
            "/alerts - Show recent alerts"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        if user.id not in ALLOWED_USERS:
            await query.edit_message_text("❌ Unauthorized")
            return
        
        callback_data = query.data
        
        if callback_data == "status":
            servers = await self.api_client.get_servers()
            if servers:
                message = "*Server Status*\n\n"
                for server in servers:
                    metric = await self.api_client.get_metrics(server['id'])
                    message += self.formatters.format_server_status(server, metric) + "\n\n"
                
                await query.edit_message_text(message, parse_mode='Markdown')
            else:
                await query.edit_message_text("⚠️ No servers found or backend is unreachable.")
        
        elif callback_data == "metrics":
            servers = await self.api_client.get_servers()
            if servers:
                keyboard = []
                for server in servers:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📊 {server['name']}",
                            callback_data=f"metrics_{server['id']}"
                        )
                    ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📊 *Select server:*",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        
        elif callback_data.startswith("metrics_"):
            server_id = int(callback_data.split("_")[1])
            metric = await self.api_client.get_metrics(server_id)
            message = self.formatters.format_metric(metric)
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif callback_data == "alerts":
            alerts = await self.api_client.get_alerts(is_acknowledged=False)
            message = self.formatters.format_alerts(alerts)
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif callback_data == "help":
            help_text = (
                "*Available Commands*\n\n"
                "🚀 *General*\n"
                "/start - Initialize bot\n"
                "/help - Show help\n\n"
                "📊 *Monitoring*\n"
                "/status - Server status\n"
                "/metrics - View metrics\n"
                "/alerts - Show alerts"
            )
            await query.edit_message_text(help_text, parse_mode='Markdown')
