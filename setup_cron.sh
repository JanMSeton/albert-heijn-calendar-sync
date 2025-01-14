#!/bin/bash

## Setup a cron job for running this script, logging succeeded runs and emailing on failure

# Get the directory of the currently executing script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove existing cron jobs for this script
crontab -l | grep -v "$script_dir/src/main.py" | crontab -

# Define log file path
LOG_FILE="$script_dir/logfile.log"
ERROR_LOG_FILE="$script_dir/error.log"

# Define email parameters
EMAIL_RECIPIENT="jans564893@gmail.com"
EMAIL_SUBJECT="albert-heijn-calender-sync Error Notification"
EMAIL_BODY="The cron job running $script_dir/src/main.py has failed. Please check the error log for details."

# Add cron job to run every Tuesday at 14:00 and send an email on failure
(crontab -l ; \
echo "0 14 * * 2 { \
  $script_dir/src/main.py >> $LOG_FILE 2>> $ERROR_LOG_FILE; \
  if [ \$? -ne 0 ]; then \
    printf "To: $EMAIL_RECIPIENT\n\nSubject: $EMAIL_SUBJECT\n\n$EMAIL_BODY" | msmtp -a default _recipient_address_$EMAIL_RECIPIENT
  fi; \
}") | sort - | uniq - | crontab -
echo "Cron jobs updated:"
crontab -l
