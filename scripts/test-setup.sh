#!/bin/bash

echo " Testing Local Log Analyzer Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
 if [ $1 -eq 0 ]; then
 echo -e " ${GREEN}$2${NC}"
 else
 echo -e " ${RED}$2${NC}"
 fi
}

print_info() {
 echo -e " ${YELLOW}$1${NC}"
}

# Test 1: Check prerequisites
echo "1. Checking Prerequisites..."
node --version > /dev/null 2>&1
print_status $? "Node.js installed"

python3 --version > /dev/null 2>&1
print_status $? "Python 3 installed"

ollama --version > /dev/null 2>&1
print_status $? "Ollama installed"

echo ""

# Test 2: Check Ollama models
echo "2. Checking Ollama Models..."
if ollama list | grep -q "codellama:13b"; then
 print_status 0 "CodeLlama 13B model available"
else
 print_status 1 "CodeLlama 13B model not found"
 print_info "Run: ollama pull codellama:13b"
fi

echo ""

# Test 3: Check Ollama service
echo "3. Checking Ollama Service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
 print_status 0 "Ollama service running on port 11434"
else
 print_status 1 "Ollama service not responding"
 print_info "Run: ollama serve"
fi

echo ""

# Test 4: Check project structure
echo "4. Checking Project Structure..."

if [ -f "frontend/package.json" ]; then
 print_status 0 "Frontend package.json exists"
else
 print_status 1 "Frontend package.json missing"
fi

if [ -f "backend/requirements.txt" ]; then
 print_status 0 "Backend requirements.txt exists"
else
 print_status 1 "Backend requirements.txt missing"
fi

if [ -d "backend/venv" ]; then
 print_status 0 "Backend virtual environment exists"
else
 print_status 1 "Backend virtual environment missing"
 print_info "Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

if [ -d "frontend/node_modules" ]; then
 print_status 0 "Frontend dependencies installed"
else
 print_status 1 "Frontend dependencies not installed"
 print_info "Run: cd frontend && npm install"
fi

echo ""

# Test 5: Test backend imports
echo "5. Testing Backend..."
cd backend
if [ -d "venv" ]; then
 source venv/bin/activate
 if python -c "from app.main import app; print('Backend imports successful')" > /dev/null 2>&1; then
 print_status 0 "Backend imports working"
 else
 print_status 1 "Backend import errors"
 fi
 
 # Test API endpoints
 if python -c "
from app.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/api/health')
assert response.status_code == 200
print('API endpoints working')
" > /dev/null 2>&1; then
 print_status 0 "Backend API endpoints working"
 else
 print_status 1 "Backend API endpoint errors"
 fi
else
 print_status 1 "Cannot test backend - virtual environment missing"
fi
cd ..

echo ""

# Test 6: Test frontend build
echo "6. Testing Frontend..."
cd frontend
if [ -d "node_modules" ]; then
 if npm run typecheck > /dev/null 2>&1; then
 print_status 0 "Frontend TypeScript compilation successful"
 else
 print_status 1 "Frontend TypeScript errors"
 fi
 
 if npm run build > /dev/null 2>&1; then
 print_status 0 "Frontend build successful"
 else
 print_status 1 "Frontend build errors"
 fi
else
 print_status 1 "Cannot test frontend - dependencies missing"
fi
cd ..

echo ""

# Test 7: Test Ollama connection
echo "7. Testing Ollama Integration..."
if curl -s -X POST http://localhost:11434/api/generate \
 -H "Content-Type: application/json" \
 -d '{"model": "codellama:13b", "prompt": "Hello", "stream": false}' \
 | grep -q '"response"'; then
 print_status 0 "Ollama CodeLlama 13B responding"
else
 print_status 1 "Ollama CodeLlama 13B not responding"
fi

echo ""
echo "🎉 Setup test complete!"
echo ""
echo "To start development:"
echo " ./scripts/start-backend.sh # Start backend API"
echo " ./scripts/start-frontend.sh # Start frontend UI"
echo " ./scripts/start-all.sh # Start everything"
echo ""
echo "Or manually:"
echo " Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo " Frontend: cd frontend && npm run dev"