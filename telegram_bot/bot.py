import logging
import httpx
import asyncio
import time
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from config.settings import TELEGRAM_BOTS, BACKEND_URL, BOT_API_CACHE_TTL
from config.bot_status import update_bot_status
from telegram_bot.handlers.server_monitoring_handlers import (
    CommandHandlers as ServerMonitoringHandlers,
    ADD_SERVER_NAME,
    ADD_SERVER_HOSTNAME,
    ADD_SERVER_PORT,
    ADD_SERVER_USERNAME,
    ADD_SERVER_PASSWORD,
)
from telegram_bot.handlers.weather_handlers import WeatherHandlers
from telegram_bot.handlers.marketprice_handlers import MarketPriceHandlers
from telegram_bot.handlers.taskmanager_handlers import TaskManagerHandlers

logger = logging.getLogger("telegram_bot")


async def _heartbeat_loop(bot_name: str):
    """Continuously mark bot as alive for backend status checks."""
    while True:
        update_bot_status(bot_name=bot_name, is_running=True)
        await asyncio.sleep(15)

class BotAPIClient:
    """Client to communicate with FastAPI backend"""
    
    def __init__(self, base_url: str = BACKEND_URL, cache_ttl: float = BOT_API_CACHE_TTL):
        self.base_url = base_url
        self.timeout = 6
        self.cache_ttl = cache_ttl
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self._cache = {}

    async def close(self):
        await self._client.aclose()

    def _get_cache(self, key):
        cached = self._cache.get(key)
        if not cached:
            return None
        expires_at, value = cached
        if time.monotonic() >= expires_at:
            self._cache.pop(key, None)
            return None
        return value

    def _set_cache(self, key, value):
        self._cache[key] = (time.monotonic() + self.cache_ttl, value)

    async def _request_json(self, method: str, path: str, **kwargs):
        response = await self._client.request(method, f"{self.base_url}{path}", **kwargs)
        return response.json() if response.status_code in (200, 201) else None
    
    async def get_servers(self):
        """Get all servers"""
        try:
            cache_key = "servers"
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            data = await self._request_json("GET", "/api/servers")
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error("Failed to get servers: %s", str(e))
            return None
    
    async def get_metrics(self, server_id: int):
        """Get latest metrics for server"""
        try:
            cache_key = f"metrics:{server_id}"
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            data = await self._request_json("GET", f"/api/metrics/{server_id}/current")
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error("Failed to get metrics: %s", str(e))
            return None
    
    async def get_alerts(self, server_id: int = None, is_acknowledged: bool = False):
        """Get recent alerts"""
        try:
            cache_key = f"alerts:{server_id}:{is_acknowledged}"
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            params = {
                'is_acknowledged': is_acknowledged,
                'limit': 10
            }
            if server_id:
                params['server_id'] = server_id
            
            response = await self._client.get(f"{self.base_url}/api/alerts", params=params)
            data = response.json() if response.status_code == 200 else None
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error("Failed to get alerts: %s", str(e))
            return None

    async def get_bots_status(self):
        """Get runtime status for all configured bots"""
        try:
            cache_key = "bots_status"
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            data = await self._request_json("GET", "/api/bots/status")
            self._set_cache(cache_key, data)
            return data
        except Exception as e:
            logger.error("Failed to get bots status: %s", str(e))
            return None
    
    async def create_user(self, telegram_user_id: str, telegram_username: str = None, telegram_first_name: str = None):
        """Register new user"""
        try:
            response = await self._client.post(
                f"{self.base_url}/api/users",
                json={
                    'telegram_user_id': telegram_user_id,
                    'telegram_username': telegram_username,
                    'telegram_first_name': telegram_first_name
                }
            )
            self._cache.pop("servers", None)
            self._cache.pop("bots_status", None)
            return response.json() if response.status_code in [200, 201] else None
        except Exception as e:
            logger.error("Failed to create user: %s", str(e))
            return None

    async def create_server(self, server_data: dict):
        """Create a new server"""
        try:
            response = await self._client.post(f"{self.base_url}/api/servers", json=server_data)
            self._cache.pop("servers", None)
            return response.json() if response.status_code in (200, 201) else None
        except Exception as e:
            logger.error("Failed to create server: %s", str(e))
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

        # Select appropriate handlers based on bot type
        if name == "server_monitoring":
            handlers = ServerMonitoringHandlers(api_client, bot_name=name)
        elif name == "weather_bot":
            handlers = WeatherHandlers(api_client, bot_name=name)
        elif name == "marketprice_bot":
            handlers = MarketPriceHandlers(api_client, bot_name=name)
        elif name == "taskmanager_bot":
            handlers = TaskManagerHandlers(api_client, bot_name=name)
        else:
            # Default to server monitoring handlers
            handlers = ServerMonitoringHandlers(api_client, bot_name=name)

        application = Application.builder().token(token).build()

        # Register handlers based on bot type
        if name == "server_monitoring":
            # Server monitoring specific commands
            application.add_handler(CommandHandler("start", handlers.start))
            application.add_handler(CommandHandler("status", handlers.status))
            application.add_handler(CommandHandler("metrics", handlers.metrics))
            application.add_handler(CommandHandler("alerts", handlers.alerts))
            application.add_handler(CommandHandler("help", handlers.help))
            application.add_handler(
                ConversationHandler(
                    entry_points=[
                        CommandHandler("addserver", handlers.add_server_start),
                        CallbackQueryHandler(handlers.add_server_start, pattern="^add_server$")
                    ],
                    states={
                        ADD_SERVER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_server_name)],
                        ADD_SERVER_HOSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_server_hostname)],
                        ADD_SERVER_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_server_port)],
                        ADD_SERVER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_server_username)],
                        ADD_SERVER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.add_server_password)],
                    },
                    fallbacks=[CommandHandler("cancel", handlers.add_server_cancel)],
                    per_chat=True,
                    per_user=True,
                )
            )
            application.add_handler(CallbackQueryHandler(handlers.button_callback))
        else:
            # Other bots: weather, market, task manager
            application.add_handler(CommandHandler("start", handlers.start))
            application.add_handler(CommandHandler("help", handlers.help))
            application.add_handler(CallbackQueryHandler(handlers.button_callback))

        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            # Keep long polling responsive. Telegram 409 conflicts are caused by
            # multiple running bot instances, not by a short poll interval.
            poll_interval=0.5,
            timeout=10,
            drop_pending_updates=True,
        )
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
            await api_client.close()
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
