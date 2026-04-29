import logging
import logging.handlers
import os
from config.settings import LOG_LEVEL, LOG_DIR

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Create formatters
formatter = logging.Formatter(LOG_FORMAT)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)

# File handler for all logs
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Specific loggers
backend_logger = logging.getLogger("backend")
backend_logger.setLevel(LOG_LEVEL)

bot_logger = logging.getLogger("telegram_bot")
bot_logger.setLevel(LOG_LEVEL)

monitoring_logger = logging.getLogger("monitoring")
monitoring_logger.setLevel(LOG_LEVEL)