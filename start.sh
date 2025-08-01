#!/bin/bash

# Navigate to bot directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the bot
echo "🚀 Starting CartoonGenieBot..."
python3 bot.py 2>&1 | tee logs.txt
