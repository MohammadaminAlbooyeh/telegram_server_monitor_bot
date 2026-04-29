#!/bin/bash
# Script to setup database

cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

source .venv/bin/activate
python -c "from backend.models.database import init_db; init_db(); print('Database initialized successfully!')"
