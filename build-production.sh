#!/bin/bash

#  Log Analysis Application - Production Build Script
# Builds optimized Docker images for production deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
 echo -e "${GREEN} $1${NC}"
}

print_info() {
 echo -e "${BLUE} $1${NC}"
}

print_warning() {
 echo -e "${YELLOW} $1${NC}"
}

print_error() {
 echo -e "${RED} $1${NC}"
}

echo "🏗️ Building Log Analysis Application for Production"
echo "================================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
 print_error "Docker is required but not installed"
 exit 1
fi

if ! command -v docker-compose &> /dev/null; then
 print_error "Docker Compose is required but not installed"
 exit 1
fi

print_status "Docker and Docker Compose are available"

# Get version tag
VERSION=${1:-"latest"}
print_info "Building version: $VERSION"

# Build backend
print_info "Building backend Docker image..."
docker build \
 -t "log-analyzer-backend:$VERSION" \
 -t "log-analyzer-backend:latest" \
 ./backend

print_status "Backend image built successfully"

# Build frontend
print_info "Building frontend Docker image..."
docker build \
 -t "log-analyzer-frontend:$VERSION" \
 -t "log-analyzer-frontend:latest" \
 ./frontend

print_status "Frontend image built successfully"

# List created images
print_info "Created Docker images:"
docker images | grep log-analyzer

echo ""
print_status "Production build completed successfully!"
echo ""

echo " Deployment Options:"
echo "====================="
echo "1. Local deployment:"
echo " docker-compose up -d"
echo ""
echo "2. Save images for distribution:"
echo " docker save log-analyzer-backend:$VERSION | gzip > backend-$VERSION.tar.gz"
echo " docker save log-analyzer-frontend:$VERSION | gzip > frontend-$VERSION.tar.gz"
echo ""
echo "3. Push to registry (if configured):"
echo " docker tag log-analyzer-backend:$VERSION your-registry/log-analyzer-backend:$VERSION"
echo " docker push your-registry/log-analyzer-backend:$VERSION"
echo " docker tag log-analyzer-frontend:$VERSION your-registry/log-analyzer-frontend:$VERSION"
echo " docker push your-registry/log-analyzer-frontend:$VERSION"
echo ""

# Optional: Run quick test
read -p "Test the built images? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
 print_info "Starting containers for testing..."
 docker-compose down --remove-orphans 2>/dev/null || true
 docker-compose up -d
 
 sleep 10 # Wait for services to start
 
 # Test backend health
 if curl -s http://localhost:8000/api/health > /dev/null; then
 print_status "Backend health check passed"
 else
 print_warning "Backend might still be starting..."
 fi
 
 # Test frontend
 if curl -s http://localhost:3000 > /dev/null; then
 print_status "Frontend is responding"
 else
 print_warning "Frontend might still be starting..."
 fi
 
 echo ""
 print_info "Test deployment running at:"
 echo "• Frontend: http://localhost:3000"
 echo "• Backend: http://localhost:8000"
 echo ""
 echo "Stop with: docker-compose down"
fi

print_status "🎉 Production build process complete!"