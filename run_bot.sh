#!/bin/bash
# Script to run the Telegram bot

cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

source .venv/bin/activate
python -m telegram_bot.bot
