import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import ALLOWED_USERS

logger = logging.getLogger("telegram_bot")

class MarketPriceHandlers:
    """Handle market price bot commands"""

    def __init__(self, api_client, bot_name: str = None):
        self.api_client = api_client
        self.bot_name = bot_name or "marketprice_bot"

    def _main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 Current Prices", callback_data="current_prices")],
            [InlineKeyboardButton("📊 Market Trends", callback_data="market_trends")],
            [InlineKeyboardButton("⭐ Watchlist", callback_data="watchlist")],
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
            logger.warning(f"Unauthorized user started market price bot {self.bot_name}: {user.id}")
            return

        # Register user
        await self.api_client.create_user(
            telegram_user_id=str(user.id),
            telegram_username=user.username,
            telegram_first_name=user.first_name
        )

        await update.message.reply_text(
            f"📈 Welcome to the Market Price Bot!\n\n"
            f"Hello {user.first_name}! I can provide you with market price information.\n\n"
            f"Use the menu below to get started:",
            reply_markup=self._main_menu_keyboard()
        )

        logger.info(f"User {user.id} started market price bot {self.bot_name}")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📈 <b>Market Price Bot Help</b>

<b>Available Commands:</b>
/start - Start the bot and show main menu
/help - Show this help message
/prices - Get current market prices
/trends - View market trends and analysis
/watchlist - Manage your price watchlist

<b>How to use:</b>
1. View current market prices
2. Add assets to your watchlist for alerts
3. Get market trend analysis and insights

<b>Note:</b> Market data is updated regularly for accuracy.
        """

        await update.message.reply_text(help_text, parse_mode="HTML")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        if query.data == "menu":
            await query.edit_message_text(
                "📈 Market Price Bot Main Menu:",
                reply_markup=self._main_menu_keyboard()
            )
        elif query.data == "current_prices":
            await query.edit_message_text(
                "📈 <b>Current Market Prices</b>\n\n"
                "Fetching latest market prices...\n\n"
                "<i>Price display functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "market_trends":
            await query.edit_message_text(
                "📊 <b>Market Trends</b>\n\n"
                "Analyzing market trends and patterns...\n\n"
                "<i>Trend analysis functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "watchlist":
            await query.edit_message_text(
                "⭐ <b>Price Watchlist</b>\n\n"
                "Manage your price alerts and watchlist.\n\n"
                "<i>Watchlist functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "help":
            help_text = """
📈 <b>Market Price Bot Help</b>

<b>Available Commands:</b>
• Current Prices - View latest market prices
• Market Trends - Analyze price movements
• Watchlist - Manage price alerts
• Help - Show this help message

<b>Note:</b> Real-time market data requires API integration.
            """
            await query.edit_message_text(help_text, parse_mode="HTML", reply_markup=self._back_keyboard())