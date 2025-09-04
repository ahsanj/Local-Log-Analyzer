#!/bin/bash

echo "  Starting Local Log Analyzer Frontend..."

cd "$(dirname "$0")/../frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
 echo " Dependencies not installed. Run 'npm install' first."
 exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
 echo " .env file not found, copying from example..."
 cp .env.example .env
fi

echo " Starting Vite development server..."
echo " Frontend: http://localhost:3000"
echo " (Vite will auto-select an available port if 3000 is busy)"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the development server
npm run dev