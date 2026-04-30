import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import ALLOWED_USERS

logger = logging.getLogger("telegram_bot")

class TaskManagerHandlers:
    """Handle task manager bot commands"""

    def __init__(self, api_client, bot_name: str = None):
        self.api_client = api_client
        self.bot_name = bot_name or "taskmanager_bot"

    def _main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 My Tasks", callback_data="my_tasks")],
            [InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
            [InlineKeyboardButton("📊 Task Stats", callback_data="task_stats")],
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
            logger.warning(f"Unauthorized user started task manager bot {self.bot_name}: {user.id}")
            return

        # Register user
        await self.api_client.create_user(
            telegram_user_id=str(user.id),
            telegram_username=user.username,
            telegram_first_name=user.first_name
        )

        await update.message.reply_text(
            f"📋 Welcome to the Task Manager Bot!\n\n"
            f"Hello {user.first_name}! I can help you manage your tasks and stay organized.\n\n"
            f"Use the menu below to get started:",
            reply_markup=self._main_menu_keyboard()
        )

        logger.info(f"User {user.id} started task manager bot {self.bot_name}")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📋 <b>Task Manager Bot Help</b>

<b>Available Commands:</b>
/start - Start the bot and show main menu
/help - Show this help message
/tasks - View your current tasks
/add - Add a new task
/done - Mark tasks as completed

<b>How to use:</b>
1. Add tasks with descriptions and due dates
2. View and manage your task list
3. Get reminders for upcoming tasks
4. Track your productivity with statistics

<b>Note:</b> Tasks are private and secure for each user.
        """

        await update.message.reply_text(help_text, parse_mode="HTML")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        if query.data == "menu":
            await query.edit_message_text(
                "📋 Task Manager Bot Main Menu:",
                reply_markup=self._main_menu_keyboard()
            )
        elif query.data == "my_tasks":
            await query.edit_message_text(
                "📝 <b>My Tasks</b>\n\n"
                "Loading your current tasks...\n\n"
                "<i>Task display functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "add_task":
            await query.edit_message_text(
                "➕ <b>Add New Task</b>\n\n"
                "Send me the task description to add it to your list.\n\n"
                "<i>Task creation functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "task_stats":
            await query.edit_message_text(
                "📊 <b>Task Statistics</b>\n\n"
                "Analyzing your task completion trends...\n\n"
                "<i>Statistics functionality will be implemented here.</i>",
                parse_mode="HTML",
                reply_markup=self._back_keyboard()
            )
        elif query.data == "help":
            help_text = """
📋 <b>Task Manager Bot Help</b>

<b>Available Commands:</b>
• My Tasks - View current task list
• Add Task - Create new tasks
• Task Stats - View productivity metrics
• Help - Show this help message

<b>Note:</b> Task management helps improve productivity.
            """
            await query.edit_message_text(help_text, parse_mode="HTML", reply_markup=self._back_keyboard())