import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import ALLOWED_USERS

logger = logging.getLogger("telegram_bot")

class WeatherHandlers:
    """Handle weather bot commands"""

    def __init__(self, api_client, bot_name: str = None):
        self.api_client = api_client
        self.bot_name = bot_name or "weather_bot"

    def _main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌤️ Current Weather", callback_data="current_weather")],
            [InlineKeyboardButton("📊 Forecast", callback_data="forecast")],
            [InlineKeyboardButton("🌍 Change Location", callback_data="change_location")],
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
            logger.warning(f"Unauthorized user started weather bot {self.bot_name}: {user.id}")
            return

        # Register user
        await self.api_client.create_user(
            telegram_user_id=str(user.id),
            telegram_username=user.username,
            telegram_first_name=user.first_name
        )

        await update.message.reply_text(
            f"🌤️ Welcome to the Weather Bot!\n\n"
            f"Hello {user.first_name}! I can provide you with weather information.\n\n"
            f"Use the menu below to get started:",
            reply_markup=self._main_menu_keyboard()
        )

        logger.info(f"User {user.id} started weather bot {self.bot_name}")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🌤️ <b>Weather Bot Help</b>

<b>Available Commands:</b>
/start - Start the bot and show main menu
/help - Show this help message
/current - Get current weather for your location
/forecast - Get weather forecast
/location - Set your location for weather updates

<b>How to use:</b>
1. Set your location using the Change Location button
2. Get current weather or forecast information
3. Receive automatic weather alerts

<b>Note:</b> Make sure your location is set for accurate weather data.
        """

        await update.message.reply_text(help_text, parse_mode="HTML")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        if query.data == "menu":
            await query.edit_message_text(
                "🌤️ Weather Bot Main Menu:",
                reply_markup=self._main_menu_keyboard()
            )
        elif query.data == "current_weather":
            await query.edit_message_text(
                "🌤️ <b>Current Weather</b>\n\n"
                "Please set your location first using the Change Location button.\n\n"
                "<i>Weather functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "forecast":
            await query.edit_message_text(
                "📊 <b>Weather Forecast</b>\n\n"
                "Please set your location first using the Change Location button.\n\n"
                "<i>Forecast functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "change_location":
            await query.edit_message_text(
                "🌍 <b>Change Location</b>\n\n"
                "Send me your city name or coordinates to set your location.\n\n"
                "<i>Location setting will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "help":
            help_text = """
🌤️ <b>Weather Bot Help</b>

<b>Available Commands:</b>
• Current Weather - Get current weather conditions
• Forecast - View weather forecast
• Change Location - Set your location
• Help - Show this help message

<b>Note:</b> Weather data requires location permission.
            """
            await query.edit_message_text(help_text, parse_mode="HTML", reply_markup=self._back_keyboard())