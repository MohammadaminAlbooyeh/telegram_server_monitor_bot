# Telegram Server Monitoring Bot

A complete monitoring system for Linux servers with a Telegram bot interface.

## Features

- Real-time server monitoring (CPU, Memory, Disk, Network)
- Telegram bot interface with inline menus
- Configurable alert thresholds
- SSH-based metrics collection
- REST API endpoints
- PostgreSQL database
- Background job scheduling

## Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and edit
3. Install dependencies: `pip install -r requirements.txt`
4. Create database: `createdb monitoring_bot`
5. Initialize database: `python scripts/setup_db.py`

## Usage

**Backend:**
```bash
python -m backend.main
```

**Bot:**
```bash
python -m telegram_bot.bot
```

**Monitoring:**
```bash
python scripts/run_monitoring.sh
```

## Docker

```bash
docker-compose up -d
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Bot Commands

- `/start` - Initialize bot
- `/status` - Show server status
- `/metrics` - View metrics
- `/alerts` - Show alerts
- `/help` - Show help