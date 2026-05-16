#!/bin/bash
# Auto-deploy script - checks for git changes and restarts service
# Run this script with cron: */5 * * * * /path/to/auto_deploy.sh

PROJECT_DIR="/path/to/your/ThaiWord"  # Change this
LOG_FILE="$PROJECT_DIR/deploy.log"

cd "$PROJECT_DIR" || exit 1

# Fetch latest changes
git fetch origin main 2>/dev/null

# Check if there are new commits
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$(date): New changes detected, deploying..." >> "$LOG_FILE"

    # Pull latest code
    git pull origin main >> "$LOG_FILE" 2>&1

    # Install dependencies
    pip install -r requirements.txt >> "$LOG_FILE" 2>&1

    # Restart service
    systemctl restart thaiword >> "$LOG_FILE" 2>&1
    # Or: pkill -f "python run.py" && cd $PROJECT_DIR && nohup python run.py &

    echo "$(date): Deployment completed" >> "$LOG_FILE"
else
    echo "$(date): No changes" >> "$LOG_FILE"
fi
