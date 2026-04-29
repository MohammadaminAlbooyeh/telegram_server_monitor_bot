import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/monitoring_bot"
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False") == "True"

# FastAPI Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False") == "True"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BOT_API_CACHE_TTL = float(os.getenv("BOT_API_CACHE_TTL", "30"))

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Authorized Telegram Users (comma-separated)
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]

# Monitoring Configuration
METRICS_COLLECTION_INTERVAL = int(os.getenv("METRICS_COLLECTION_INTERVAL", "300"))
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "120"))
METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))

# Alert Thresholds (defaults)
DEFAULT_CPU_THRESHOLD = float(os.getenv("DEFAULT_CPU_THRESHOLD", "80"))
DEFAULT_MEMORY_THRESHOLD = float(os.getenv("DEFAULT_MEMORY_THRESHOLD", "85"))
DEFAULT_DISK_THRESHOLD = float(os.getenv("DEFAULT_DISK_THRESHOLD", "90"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# SSH Configuration
SSH_TIMEOUT = int(os.getenv("SSH_TIMEOUT", "10"))
SSH_RETRIES = int(os.getenv("SSH_RETRIES", "3"))

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Multiple Telegram Bots Configuration
WEATHERBOT_TOKEN = os.getenv("WEATHERBOT_TOKEN", "")
MARKETPRICEBOT_TOKEN = os.getenv("MARKETPRICEBOT_TOKEN", "")
TASKMANAGERBOT_TOKEN = os.getenv("TASKMANAGERBOT_TOKEN", "")

TELEGRAM_BOTS = {
    "main": TELEGRAM_BOT_TOKEN,
    "weatherbot": WEATHERBOT_TOKEN,
    "marketpricebot": MARKETPRICEBOT_TOKEN,
    "taskmanagerbot": TASKMANAGERBOT_TOKEN,
}

# Filter out empty tokens
TELEGRAM_BOTS = {name: token for name, token in TELEGRAM_BOTS.items() if token}

# Bot runtime status shared file (used by both backend and bot process)
BOT_STATUS_FILE = os.getenv("BOT_STATUS_FILE", str(BASE_DIR / "runtime" / "bot_status.json"))
BOT_HEARTBEAT_STALE_SECONDS = int(os.getenv("BOT_HEARTBEAT_STALE_SECONDS", "90"))
