#!/bin/bash

echo " Starting Local Log Analyzer Backend..."

cd "$(dirname "$0")/../backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
 echo " Virtual environment not found. Run setup.sh first."
 exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
 echo " .env file not found, copying from example..."
 cp ../.env.example .env
fi

# Create uploads directory
mkdir -p uploads

echo " Starting FastAPI development server..."
echo " Backend: http://localhost:8000"
echo " API Docs: http://localhost:8000/api/docs"
echo " Health Check: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000