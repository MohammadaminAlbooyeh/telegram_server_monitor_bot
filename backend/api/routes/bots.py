"""API routes for bot information"""
from fastapi import APIRouter
import logging
from datetime import datetime, timezone

from config.settings import TELEGRAM_BOTS, BOT_HEARTBEAT_STALE_SECONDS
from config.bot_status import read_bot_status

logger = logging.getLogger("backend")

router = APIRouter(tags=["bots"])


@router.get("/bots")
async def list_bots():
    """
    Return configured bots and their status.

    Returns list of bot configurations with masked tokens.
    """
    bots = []

    # Add all bot configurations
    for name, token in TELEGRAM_BOTS.items():
        bots.append({
            "name": name,
            "configured": bool(token),
            "token_masked": (token[:6] + "..." if token else ""),
            "type": name
        })

    return {
        "bots": bots,
        "total": len(bots),
        "active": sum(1 for bot in bots if bot["configured"])
    }


@router.get("/bots/status")
async def bots_status():
    """
    Get detailed status of all configured bots.
    """
    runtime_status = read_bot_status().get("bots", {})
    now = datetime.now(timezone.utc)
    bots = {}

    for name, token in TELEGRAM_BOTS.items():
        bot_runtime = runtime_status.get(name, {})
        last_heartbeat = bot_runtime.get("last_heartbeat")
        heartbeat_age_seconds = None
        is_up = False

        if isinstance(last_heartbeat, str):
            try:
                heartbeat_dt = datetime.fromisoformat(last_heartbeat)
                if heartbeat_dt.tzinfo is None:
                    heartbeat_dt = heartbeat_dt.replace(tzinfo=timezone.utc)
                heartbeat_age_seconds = (now - heartbeat_dt).total_seconds()
                is_up = (
                    bool(bot_runtime.get("is_running"))
                    and heartbeat_age_seconds <= BOT_HEARTBEAT_STALE_SECONDS
                )
            except ValueError:
                is_up = False

        bots[name] = {
            "configured": bool(token),
            "state": "up" if is_up else "down",
            "is_up": is_up,
            "last_heartbeat": last_heartbeat,
            "heartbeat_age_seconds": heartbeat_age_seconds,
            "error": bot_runtime.get("error"),
        }

    return {
        "bots_configured": len(TELEGRAM_BOTS),
        "stale_after_seconds": BOT_HEARTBEAT_STALE_SECONDS,
        "bots": bots,
        "up_count": sum(1 for bot in bots.values() if bot["is_up"]),
        "down_count": sum(1 for bot in bots.values() if not bot["is_up"]),
    }
