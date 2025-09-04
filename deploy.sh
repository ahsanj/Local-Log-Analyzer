#!/bin/bash

#  Log Analysis Application - One-Click Deployment Script
# This script deploys the Local Log Analysis Application with AI chat features

set -e  # Exit on any error

echo " Starting Log Analysis Application Deployment..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
 echo -e "${GREEN} $1${NC}"
}

print_warning() {
 echo -e "${YELLOW} $1${NC}"
}

print_error() {
 echo -e "${RED} $1${NC}"
}

print_info() {
 echo -e "${BLUE} $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
 print_error "Docker is not installed. Please install Docker first:"
 echo "https://docs.docker.com/get-docker/"
 exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
 print_error "Docker Compose is not installed. Please install Docker Compose first:"
 echo "https://docs.docker.com/compose/install/"
 exit 1
fi

print_status "Docker and Docker Compose are installed"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
 print_warning "Ollama is not installed. Installing Ollama..."
 curl -fsSL https://ollama.com/install.sh | sh
 print_status "Ollama installed successfully"
else
 print_status "Ollama is already installed"
fi

# Check if CodeLlama model is available
print_info "Checking for CodeLlama 13B model..."
if ! ollama list | grep -q "codellama:13b-instruct"; then
 print_warning "CodeLlama 13B model not found. Downloading (this may take a while)..."
 ollama pull codellama:13b-instruct
 print_status "CodeLlama 13B model downloaded successfully"
else
 print_status "CodeLlama 13B model is already available"
fi

# Start Ollama service in background
print_info "Starting Ollama service..."
nohup ollama serve > ollama.log 2>&1 &
OLLAMA_PID=$!
sleep 5 # Give Ollama time to start

# Test Ollama connection
if curl -s http://localhost:11434/api/version > /dev/null; then
 print_status "Ollama service is running"
else
 print_error "Failed to start Ollama service"
 exit 1
fi

# Build and start the application
print_info "Building and starting the application..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose up --build -d

# Wait for services to be healthy
print_info "Waiting for services to start..."
sleep 30

# Check service status
print_info "Checking service status..."

# Check backend health
if curl -s http://localhost:8000/api/health > /dev/null; then
 print_status "Backend API is running (http://localhost:8000)"
else
 print_warning "Backend API might still be starting..."
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
 print_status "Frontend is running (http://localhost:3000)"
else
 print_warning "Frontend might still be starting..."
fi

# Display service URLs
echo ""
echo " Deployment Complete!"
echo "======================"
print_status "Frontend Application: http://localhost:3000"
print_status "Backend API: http://localhost:8000"
print_status "API Documentation: http://localhost:8000/api/docs"
echo ""

# Display useful commands
echo " Useful Commands:"
echo "==================="
echo "• View logs: docker-compose logs -f"
echo "• Stop services: docker-compose down"
echo "• Restart services: docker-compose restart"
echo "• Check Ollama: ollama list"
echo "• Service status: docker-compose ps"
echo ""

# Display system info
echo "💻 System Information:"
echo "======================"
echo "• Ollama PID: $OLLAMA_PID"
echo "• Available models: $(ollama list | grep codellama || echo 'None')"
echo "• Docker containers: $(docker-compose ps --services | wc -l) services running"
echo ""

print_status " Ready to analyze logs with AI!"
print_info "Open http://localhost:3000 in your browser to get started"

# Optional: Open browser automatically (macOS/Linux)
if command -v open &> /dev/null; then
 read -p "Open browser automatically? (y/n): " -n 1 -r
 echo
 if [[ $REPLY =~ ^[Yy]$ ]]; then
 open http://localhost:3000
 fi
elif command -v xdg-open &> /dev/null; then
 read -p "Open browser automatically? (y/n): " -n 1 -r
 echo
 if [[ $REPLY =~ ^[Yy]$ ]]; then
 xdg-open http://localhost:3000
 fi
fi