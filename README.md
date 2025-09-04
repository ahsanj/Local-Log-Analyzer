# Local Log Analyzer

A privacy-first, local log analysis application that enables users to upload and analyze log files using a locally-running LLM (CodeLlama 13B via Ollama). The application provides intelligent log parsing, pattern recognition, and conversational analysis capabilities without sending sensitive data to external services.

## Key Features

- **Privacy & Security**: All data processing occurs locally - no cloud dependencies
- **Cost Efficient**: No API costs - uses local LLM inference via Ollama
- **AI-Powered Chat**: Natural language conversations with your logs using CodeLlama 13B
- **Persistent Sessions**: Chat history and analysis persist across view switches and app restarts
- **Comprehensive Analysis**: Error detection, pattern recognition, anomaly identification, timeline charts
- **Multi-Format Support**: .log, .txt, .json, .csv, .syslog files up to 100MB
- **Fast Processing**: Optimized parsing and analysis with real-time feedback
- **One-Click Deploy**: Automated installation and setup scripts
- **Container Ready**: Production-ready Docker deployment

## Architecture

```
Frontend (React + TypeScript) <-> Backend (FastAPI + Python) <-> Ollama (CodeLlama 13B)
```

## Prerequisites

Before setting up the application, ensure you have:

- **Node.js 18+** for frontend development
- **Python 3.9+** for backend development
- **Ollama** with CodeLlama 13B model
- **8GB+ RAM** (recommended for optimal performance)

### Installing Ollama and CodeLlama

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows
   # Download from https://ollama.ai/download/windows
   ```

2. **Pull CodeLlama 13B model**:
   ```bash
   ollama pull codellama:13b
   ```

3. **Start Ollama service**:
   ```bash
   ollama serve
   ```

## Quick Start

### Option 1: One-Click Deployment (Recommended)
The fastest way to get started:

```bash
# Download and run the deployment script
curl -fsSL https://your-repo.com/deploy.sh | bash
```

This automatically:
- Installs Ollama and CodeLlama 13B model
- Builds and starts all services with Docker
- Opens the application in your browser

**That's it!** Your application will be running at `http://localhost:3000`

### Option 2: Manual Docker Deployment
If you prefer manual control:

```bash
# Clone the repository
git clone <repository-url>
cd loganalysis

# Install Ollama and CodeLlama model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull codellama:13b-instruct
ollama serve &

# Start the application
docker-compose up -d

# Open in browser
open http://localhost:3000
```

### Option 3: Development Setup
For developers who want to modify the code:

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
mkdir uploads
python -m app.main
```

#### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Quick Verification
1. Open `http://localhost:3000` in your browser
2. Upload a sample log file
3. Ask the AI: "What errors are in these logs?"
4. Check that chat history persists when switching views

## Usage

### Uploading Log Files

1. **Drag & Drop**: Simply drag a log file onto the upload area
2. **File Browser**: Click to browse and select files
3. **Paste Content**: Copy and paste log content directly

**Supported formats**: `.log`, `.txt`, `.csv`, `.json`, `.syslog`
**Maximum file size**: 50MB

### Analyzing Logs

Once uploaded, the application automatically:

- **Parses** log entries with timestamp and level detection
- **Identifies** error patterns and anomalies
- **Generates** timeline visualizations
- **Provides** conversational AI analysis

### Chat Interface

Ask natural language questions like:
- "What are the most common errors?"
- "Show me errors from the last hour"
- "Which service has the most critical issues?"
- "Are there any unusual patterns?"

## Configuration

### Backend Configuration

Edit `backend/.env`:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000

# Ollama settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=codellama:13b

# File upload limits
MAX_FILE_SIZE=52428800  # 50MB

# Analysis settings
MAX_LOG_ENTRIES=100000
```

### Frontend Configuration

Edit `frontend/.env`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
loganalysis/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript definitions
│   │   └── utils/          # Utility functions
│   ├── package.json
│   └── vite.config.ts
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── requirements.txt
│   └── main.py
├── docs/                   # Documentation
├── scripts/               # Setup scripts
└── README.md
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
cd backend
black app/
isort app/

# Frontend
cd frontend
npm run lint
```

### Building for Production

```bash
# Frontend build
cd frontend
npm run build

# Backend with gunicorn
cd backend
gunicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker Support

### Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -t log-analyzer-backend ./backend
docker build -t log-analyzer-frontend ./frontend
```

### Production Deployment
```bash
# Build optimized production images
./build-production.sh v1.0

# Deploy with production configuration
docker-compose up -d
```

## Distribution

### For End Users
Create a distribution package:
```bash
# Create release package
./create-release.sh v1.0

# Share the generated file: log-analyzer-v1.0.tar.gz
# Users install with: ./install.sh
```

### For Organizations
Multiple deployment options available:
- **Docker Images**: Ready-to-deploy containers
- **Cloud Deployment**: AWS, GCP, Azure compatible
- **Enterprise Features**: Custom branding, SSO integration

Contact support for enterprise deployment guides.

## Log Format Support

### Automatic Detection

The application automatically detects:

- **JSON logs**: Structured JSON per line
- **CSV logs**: Comma-separated values with headers  
- **Syslog**: Standard syslog format
- **Plain text**: Unstructured text logs

### Custom Parsing

For custom log formats, the parser attempts to extract:

- **Timestamps**: Various formats (ISO 8601, Unix, etc.)
- **Log levels**: ERROR, WARN, INFO, DEBUG, etc.
- **Services**: Component/service identifiers
- **Messages**: Main log content

## Analysis Features

### Pattern Detection

- **Error patterns**: Common error types and frequencies
- **Repetitive messages**: Recurring log entries
- **Service patterns**: Service-specific behaviors
- **Time-based patterns**: Temporal anomalies

### Anomaly Detection

- **Volume spikes**: Unusual log volumes
- **Error bursts**: Concentrated error periods
- **Silence gaps**: Missing log periods
- **Service anomalies**: Unusual service behaviors

### Visualizations

- **Timeline charts**: Log activity over time
- **Level distribution**: Error/Warning/Info breakdown
- **Service breakdown**: Activity by component
- **Pattern frequencies**: Most common issues

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


---

**Built for privacy-conscious developers**