#!/bin/sh

export TZ="America/New_York"

while :
do
  # Calculate seconds until 16:30 today or tomorrow
  now=$(date +%s)
  today_target=$(date -d "$(date +%Y-%m-%d) 16:30:00" +%s)

  if [ $now -lt $today_target ]; then
    # Target time is today
    sleep_seconds=$((today_target - now))
  else
    # Target time is tomorrow
    tomorrow=$(date -d "tomorrow" +%Y-%m-%d)
    tomorrow_target=$(date -d "$tomorrow 16:30:00" +%s)
    sleep_seconds=$((tomorrow_target - now))
  fi

  echo "Sleeping for $sleep_seconds seconds until next scheduled run at 16:30"
  sleep $sleep_seconds

  # Run the scraper
  echo "Starting scraper at $(date)"
  cd /app && python3 -m scraper
  echo "Scraper finished at $(date)"
done
