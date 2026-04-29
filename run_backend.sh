#!/bin/bash
# Script to run the backend server

cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

source .venv/bin/activate
python -m backend.main
