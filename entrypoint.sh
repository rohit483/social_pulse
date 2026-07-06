#!/bin/bash
set -e

echo "Starting Social Pulse container..."

# Check if cookie.json exists and actually contains data (more than just '[]')
if [ -f "cookie.json" ] && [ $(wc -c < "cookie.json") -gt 10 ]; then
    echo "Running session extraction from cookie.json..."
    python extract_sessions.py
else
    echo "No valid cookie.json found. Assuming sessions are already set in .env."
fi

# Start the Flask application
echo "Starting Flask application..."
exec python app.py
