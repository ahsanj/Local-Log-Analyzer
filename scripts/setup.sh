#!/bin/bash

# Local Log Analyzer Setup Script
set -e

echo " Setting up Local Log Analyzer..."

# Check prerequisites
check_prerequisites() {
 echo " Checking prerequisites..."
 
 # Check Node.js
 if ! command -v node &> /dev/null; then
 echo " Node.js is required but not installed. Please install Node.js 18+ and try again."
 exit 1
 fi
 
 NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
 if [ "$NODE_VERSION" -lt 18 ]; then
 echo " Node.js 18+ is required. Current version: $(node --version)"
 exit 1
 fi
 echo " Node.js $(node --version) found"
 
 # Check Python
 if ! command -v python3 &> /dev/null; then
 echo " Python 3 is required but not installed. Please install Python 3.9+ and try again."
 exit 1
 fi
 
 PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
 echo " Python $(python3 --version) found"
 
 # Check Ollama
 if ! command -v ollama &> /dev/null; then
 echo " Ollama not found. Please install Ollama first:"
 echo " macOS: brew install ollama"
 echo " Linux: curl -fsSL https://ollama.ai/install.sh | sh"
 echo " Windows: Download from https://ollama.ai/"
 exit 1
 fi
 echo " Ollama found"
}

# Setup backend
setup_backend() {
 echo " Setting up Python backend..."
 
 cd backend
 
 # Create virtual environment
 if [ ! -d "venv" ]; then
 python3 -m venv venv
 echo " Virtual environment created"
 fi
 
 # Activate virtual environment
 source venv/bin/activate
 
 # Install dependencies
 pip install --upgrade pip
 pip install -r requirements.txt
 echo " Python dependencies installed"
 
 # Create environment file
 if [ ! -f ".env" ]; then
 cp ../.env.example .env
 echo " Environment file created"
 fi
 
 # Create uploads directory
 mkdir -p uploads
 echo " Uploads directory created"
 
 cd ..
}

# Setup frontend
setup_frontend() {
 echo " Setting up React frontend..."
 
 cd frontend
 
 # Install dependencies
 npm install
 echo " Node.js dependencies installed"
 
 # Create environment file
 if [ ! -f ".env" ]; then
 cp .env.example .env
 echo " Environment file created"
 fi
 
 cd ..
}

# Check Ollama model
check_ollama_model() {
 echo " Checking Ollama CodeLlama model..."
 
 # Check if Ollama service is running
 if ! pgrep -f "ollama" > /dev/null; then
 echo " Ollama service is not running. Starting Ollama..."
 ollama serve &
 sleep 5
 fi
 
 # Check if CodeLlama model is available
 if ! ollama list | grep -q "codellama:13b"; then
 echo " CodeLlama 13B model not found. Downloading..."
 echo " This may take several minutes (7GB download)..."
 ollama pull codellama:13b
 echo " CodeLlama 13B model downloaded"
 else
 echo " CodeLlama 13B model already available"
 fi
}

# Create startup scripts
create_scripts() {
 echo " Creating startup scripts..."
 
 # Backend start script
 cat > scripts/start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
python -m app.main
EOF
 chmod +x scripts/start-backend.sh
 
 # Frontend start script
 cat > scripts/start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF
 chmod +x scripts/start-frontend.sh
 
 # Combined start script
 cat > scripts/start-all.sh << 'EOF'
#!/bin/bash
echo " Starting Local Log Analyzer..."

# Start Ollama if not running
if ! pgrep -f "ollama" > /dev/null; then
 echo "Starting Ollama service..."
 ollama serve &
 sleep 3
fi

# Start backend in background
echo "Starting backend..."
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Start frontend
echo "Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo " All services started!"
echo " Backend: http://localhost:8000"
echo " Frontend: http://localhost:3000"
echo " API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null' EXIT
wait
EOF
 chmod +x scripts/start-all.sh
 
 echo " Startup scripts created"
}

# Main setup function
main() {
 # Create scripts directory if it doesn't exist
 mkdir -p scripts
 
 check_prerequisites
 setup_backend
 setup_frontend
 check_ollama_model
 create_scripts
 
 echo ""
 echo " Setup completed successfully!"
 echo ""
 echo " Next steps:"
 echo " 1. Start all services: ./scripts/start-all.sh"
 echo " 2. Or start individually:"
 echo " - Backend: ./scripts/start-backend.sh"
 echo " - Frontend: ./scripts/start-frontend.sh"
 echo " 3. Open http://localhost:3000 in your browser"
 echo ""
 echo " For more information, see README.md"
}

# Run main function
main "$@"