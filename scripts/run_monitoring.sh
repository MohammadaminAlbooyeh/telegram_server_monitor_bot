#!/bin/bash
python -c "from monitoring.schedulers import start_scheduler; start_scheduler(); import time; time.sleep(999999)"