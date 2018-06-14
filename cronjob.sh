#!/bin/bash

# To run this script as a cron job use: "crontab -e"
# Then input: */5 * * * * ~/git/GarageDoorOpener/cronjob.sh
# This will run the cronjob.sh script every 5 minutes.

process=$(ps | grep "raspi_master.py" | grep -v grep | awk '{print $1}')

# If the process is NOT running...
if [[ $process = "" ]]
then
    # Restart the program
    python3 ~/git/GarageDoorOpener/raspi_master.py &
fi
