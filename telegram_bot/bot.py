import logging
import httpx
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config.settings import TELEGRAM_BOTS, BACKEND_URL
from config.bot_status import update_bot_status
from telegram_bot.handlers.command_handlers import CommandHandlers

logger = logging.getLogger("telegram_bot")


async def _heartbeat_loop(bot_name: str):
    """Continuously mark bot as alive for backend status checks."""
    while True:
        update_bot_status(bot_name=bot_name, is_running=True)
        await asyncio.sleep(15)

class BotAPIClient:
    """Client to communicate with FastAPI backend"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.timeout = 10
    
    async def get_servers(self):
        """Get all servers"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/servers")
                return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error("Failed to get servers: %s", str(e))
            return None
    
    async def get_metrics(self, server_id: int):
        """Get latest metrics for server"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/metrics/{server_id}/current")
                return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error("Failed to get metrics: %s", str(e))
            return None
    
    async def get_alerts(self, server_id: int = None, is_acknowledged: bool = False):
        """Get recent alerts"""
        try:
            params = {
                'is_acknowledged': is_acknowledged,
                'limit': 10
            }
            if server_id:
                params['server_id'] = server_id
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/alerts", params=params)
                return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error("Failed to get alerts: %s", str(e))
            return None
    
    async def create_user(self, telegram_user_id: str, telegram_username: str = None, telegram_first_name: str = None):
        """Register new user"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/users",
                    json={
                        'telegram_user_id': telegram_user_id,
                        'telegram_username': telegram_username,
                        'telegram_first_name': telegram_first_name
                    }
                )
                return response.json() if response.status_code in [200, 201] else None
        except Exception as e:
            logger.error("Failed to create user: %s", str(e))
            return None


async def _run_single_bot(name: str, token: str):
    """Create and run one bot application."""
    if not token:
        logger.info("Bot '%s' token empty — skipping", name)
        return

    logger.info("Starting bot '%s'", name)
    update_bot_status(bot_name=name, is_running=False, error=None)
    try:
        api_client = BotAPIClient(base_url=BACKEND_URL)
        handlers = CommandHandlers(api_client, bot_name=name)

        application = Application.builder().token(token).build()

        # Register same command handlers for each bot instance
        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("status", handlers.status))
        application.add_handler(CommandHandler("metrics", handlers.metrics))
        application.add_handler(CommandHandler("alerts", handlers.alerts))
        application.add_handler(CommandHandler("help", handlers.help))
        application.add_handler(CallbackQueryHandler(handlers.button_callback))

        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        update_bot_status(bot_name=name, is_running=True, error=None)
        logger.info("Bot '%s' is running", name)

        heartbeat_task = asyncio.create_task(_heartbeat_loop(name))
        # keep running until cancelled
        try:
            await asyncio.Event().wait()
        finally:
            logger.info("Shutting down bot '%s'", name)
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            update_bot_status(bot_name=name, is_running=False, error=None)
    except Exception as e:
        logger.error("Error running bot '%s': %s", name, str(e))
        update_bot_status(bot_name=name, is_running=False, error=str(e))


async def main():
    """Main function to run all configured bots concurrently"""
    logger.info("Initializing %d Telegram bot(s)...", len(TELEGRAM_BOTS))
    
    tasks = []
    for name, token in TELEGRAM_BOTS.items():
        if token:
            tasks.append(asyncio.create_task(_run_single_bot(name, token)))
        else:
            logger.warning("No token configured for bot '%s' — not starting it", name)

    if not tasks:
        logger.error("No bot tokens configured. Exiting.")
        return

    logger.info("All configured bots started. Running...")
    # Wait for all bots (they run until cancelled)
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")