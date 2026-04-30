import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import ALLOWED_USERS
from telegram_bot.formatters import BotFormatters
from backend.schemas.server import ServerCreate

logger = logging.getLogger("telegram_bot")

ADD_SERVER_NAME, ADD_SERVER_HOSTNAME, ADD_SERVER_PORT, ADD_SERVER_USERNAME, ADD_SERVER_PASSWORD = range(5)

class CommandHandlers:
    """Handle bot commands"""
    
    def __init__(self, api_client, bot_name: str = None):
        self.api_client = api_client
        self.bot_name = bot_name or "telegram_bot"
        self.formatters = BotFormatters()

    def _main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Status", callback_data="status")],
            [InlineKeyboardButton("📈 Metrics", callback_data="metrics")],
            [InlineKeyboardButton("⚠️ Alerts", callback_data="alerts")],
            [InlineKeyboardButton("➕ Add Server", callback_data="add_server")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ])

    def _back_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="menu")]
        ])
    
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
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=self._main_menu_keyboard()
        )
        logger.info(f"User started bot: {user.id}")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        
        if user.id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Unauthorized")
            return
        
        await update.message.reply_text("🔄 Loading bot status...")

        try:
            bots_status = await self.api_client.get_bots_status()
            if not bots_status:
                await update.message.reply_text("⚠️ Bot status is unavailable or backend is unreachable.")
                return

            message = self.formatters.format_bots_status(bots_status)

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=self._back_keyboard()
            )
        except Exception as e:
            logger.error("Failed to build /status response for %s: %s", self.bot_name, str(e))
            await update.message.reply_text("❌ Error loading status. Please try again.")
    
    async def metrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /metrics command"""
        user = update.effective_user
        
        if user.id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Unauthorized")
            return

        loading_message = await update.message.reply_text("🔄 Loading servers...")
        
        servers = await self.api_client.get_servers()
        
        if servers is None:
            await loading_message.edit_text("⚠️ Backend is unreachable.")
            return

        if not servers:
            await loading_message.edit_text("❌ No servers configured.")
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
        await loading_message.edit_text(
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
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=self._back_keyboard()
        )
    
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
            "/alerts - Show recent alerts\n"
            "/addserver - Add a new server"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=self._back_keyboard()
        )
    
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
            bots_status = await self.api_client.get_bots_status()
            if bots_status:
                message = self.formatters.format_bots_status(bots_status)
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=self._back_keyboard()
                )
            else:
                await query.edit_message_text("⚠️ Bot status is unavailable or backend is unreachable.")
        
        elif callback_data == "metrics":
            await query.edit_message_text("🔄 Loading metrics...")
            servers = await self.api_client.get_servers()
            if servers is None:
                await query.edit_message_text(
                    "⚠️ Backend is unreachable.",
                    reply_markup=self._back_keyboard()
                )
            elif servers:
                keyboard = []
                for server in servers:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📊 {server['name']}",
                            callback_data=f"metrics_{server['id']}"
                        )
                    ])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📊 *Select server:*",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    "❌ No servers configured.",
                    reply_markup=self._back_keyboard()
                )
        
        elif callback_data.startswith("metrics_"):
            server_id = int(callback_data.split("_")[1])
            await query.edit_message_text("🔄 Loading server metrics...")
            metric = await self.api_client.get_metrics(server_id)
            message = self.formatters.format_metric(metric)
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=self._back_keyboard()
            )
        
        elif callback_data == "alerts":
            alerts = await self.api_client.get_alerts(is_acknowledged=False)
            message = self.formatters.format_alerts(alerts)
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=self._back_keyboard()
            )
        
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
            await query.edit_message_text(
                help_text,
                parse_mode='Markdown',
                reply_markup=self._back_keyboard()
            )
        
        elif callback_data == "add_server":
            await query.edit_message_text(
                "➕ *Add Server*\n\nSend the server name:",
                parse_mode='Markdown'
            )
            return ADD_SERVER_NAME

        elif callback_data == "menu":
            await query.edit_message_text(
                "🏠 *Main Menu*\n\nChoose an option:",
                parse_mode='Markdown',
                reply_markup=self._main_menu_keyboard()
            )

    async def add_server_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start add-server conversation"""
        user = update.effective_user
        if user.id not in ALLOWED_USERS:
            if update.message:
                await update.message.reply_text("❌ Unauthorized")
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text("❌ Unauthorized")
            return

        context.user_data["new_server"] = {}
        prompt = "➕ *Add Server*\n\nSend the server name:"
        if update.message:
            await update.message.reply_text(prompt, parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(prompt, parse_mode='Markdown')
        return ADD_SERVER_NAME

    async def add_server_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = update.message.text.strip()
        context.user_data["new_server"]["name"] = name
        await update.message.reply_text("Send the hostname or IP address:")
        return ADD_SERVER_HOSTNAME

    async def add_server_hostname(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        hostname = update.message.text.strip()
        context.user_data["new_server"]["hostname"] = hostname
        await update.message.reply_text("Send the SSH port (or type `22`):", parse_mode='Markdown')
        return ADD_SERVER_PORT

    async def add_server_port(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            ssh_port = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("Please send a valid port number.")
            return ADD_SERVER_PORT

        context.user_data["new_server"]["ssh_port"] = ssh_port
        await update.message.reply_text("Send the SSH username:")
        return ADD_SERVER_USERNAME

    async def add_server_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip()
        context.user_data["new_server"]["username"] = username
        await update.message.reply_text("Send the SSH password:")
        return ADD_SERVER_PASSWORD

    async def add_server_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        password = update.message.text.strip()
        data = context.user_data.get("new_server", {})
        data["password"] = password
        data.setdefault("is_active", True)
        data.setdefault("ssh_port", 22)

        try:
            server = ServerCreate(**data)
            result = await self.api_client.create_server(server.model_dump())
            if result:
                await update.message.reply_text(
                    f"✅ Server *{result['name']}* added successfully.",
                    parse_mode='Markdown',
                    reply_markup=self._main_menu_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ Failed to add server.",
                    reply_markup=self._main_menu_keyboard()
                )
        except Exception as e:
            logger.error("Failed to add server: %s", str(e))
            await update.message.reply_text(
                "❌ Invalid server data. Please try again.",
                reply_markup=self._main_menu_keyboard()
            )
        finally:
            context.user_data.pop("new_server", None)
        return -1

    async def add_server_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.pop("new_server", None)
        await update.message.reply_text("Cancelled.", reply_markup=self._main_menu_keyboard())
        return -1
