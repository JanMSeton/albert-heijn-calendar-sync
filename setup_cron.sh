#!/bin/bash

## Setup a cron job for running this script, logging succeeded runs

# Get the directory of the currently executing script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove existing cron jobs for this script
crontab -l | grep -v "$script_dir/src/main.py" | crontab -

# Define log file path
LOG_FILE="/path/to/your/logfile.log"

# Add cron jobs for the first Monday of every month at 14:00
(crontab -l ; echo "0 14 * * 1 [ \"\$(date +\%a)\" == \"Mon\" ] && $script_dir/src/main.py >> $LOG_FILE 2>&1") | sort - | uniq - | crontab -

echo "Cron jobs updated:"
crontab -l
