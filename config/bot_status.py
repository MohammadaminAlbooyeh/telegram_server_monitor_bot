import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from config.settings import BOT_STATUS_FILE


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_path() -> Path:
    return Path(BOT_STATUS_FILE)


def read_bot_status() -> Dict[str, Any]:
    path = _status_path()
    if not path.exists():
        return {"bots": {}}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "bots" in data and isinstance(data["bots"], dict):
                return data
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass

    return {"bots": {}}


def write_bot_status(data: Dict[str, Any]) -> None:
    path = _status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)


def update_bot_status(bot_name: str, is_running: bool, error: str | None = None) -> None:
    data = read_bot_status()
    data.setdefault("bots", {})
    data["bots"][bot_name] = {
        "is_running": bool(is_running),
        "last_heartbeat": _utc_now_iso(),
        "error": error,
    }
    data["updated_at"] = _utc_now_iso()
    write_bot_status(data)
