#!/bin/bash

echo " Testing Ollama Integration for Log Analysis"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
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
 echo -e " ${BLUE}$1${NC}"
}

print_section() {
 echo -e "\n ${YELLOW}$1${NC}"
 echo "----------------------------------------"
}

# Check if we're in the right directory
if [ ! -f "app/services/chat_service.py" ]; then
 echo " Please run this script from the backend directory"
 exit 1
fi

print_section "Checking Ollama Service"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
 print_status 0 "Ollama is running"
 
 # Check if CodeLlama 13B is available
 if curl -s http://localhost:11434/api/tags | grep -q "codellama:13b"; then
 print_status 0 "CodeLlama 13B model is available"
 else
 print_status 1 "CodeLlama 13B model not found"
 print_info "Run: ollama pull codellama:13b"
 exit 1
 fi
else
 print_status 1 "Ollama is not running"
 print_info "Start Ollama with: ollama serve"
 exit 1
fi

print_section "Testing Basic Integration"

# Run basic integration test
print_info "Running Ollama integration test..."
if python test_ollama_integration.py > /tmp/ollama_test.log 2>&1; then
 print_status 0 "Basic integration test passed"
else
 print_status 1 "Basic integration test failed"
 echo "Error details:"
 tail -10 /tmp/ollama_test.log
 exit 1
fi

print_section "Testing Log Processing Integration"

# Check if sample logs exist
if [ -d "../sample_logs" ]; then
 print_status 0 "Sample log files found"
 
 # Run simple integration test
 print_info "Testing file processing + AI analysis..."
 if python test_simple_integration.py > /tmp/integration_test.log 2>&1; then
 print_status 0 "Log processing integration test passed"
 else
 print_status 1 "Log processing integration test failed"
 echo "Error details:"
 tail -10 /tmp/integration_test.log
 fi
else
 print_status 1 "Sample log files not found"
 print_info "Sample logs should be in ../sample_logs/"
fi

print_section "Testing Different Log Formats"

# Test each format individually
formats=("JSON" "CSV" "Syslog" "Plain Text")
files=("api_logs.json" "access.csv" "system.syslog" "application.log")

for i in ${!formats[@]}; do
 format=${formats[$i]}
 file=${files[$i]}
 
 if [ -f "../sample_logs/$file" ]; then
 print_info "Testing $format format..."
 
 # Quick test with Python
 result=$(python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.file_processor import FileProcessor

async def test():
 fp = FileProcessor()
 with open('../sample_logs/$file', 'r') as f:
 content = f.read()
 entries, fmt = await fp.process_content(content, '$file')
 return len(entries)

print(asyncio.run(test()))
" 2>/dev/null)
 
 if [ $? -eq 0 ] && [ "$result" -gt 0 ]; then
 print_status 0 "$format format: $result entries parsed"
 else
 print_status 1 "$format format parsing failed"
 fi
 else
 print_status 1 "$format sample file not found"
 fi
done

print_section "Performance Test"

# Simple performance test
print_info "Testing response time..."
start_time=$(date +%s.%3N)

response_time=$(python3 -c "
import asyncio
import time
import sys
sys.path.insert(0, '.')
from app.services.chat_service import ChatService

async def perf_test():
 cs = ChatService()
 start = time.time()
 await cs.generate_response('Analyze log patterns', {'total_entries': 100})
 return round(time.time() - start, 2)

print(asyncio.run(perf_test()))
" 2>/dev/null)

if [ $? -eq 0 ]; then
 print_status 0 "Response generated in ${response_time}s"
 
 # Performance feedback
 if (( $(echo "$response_time < 5.0" | bc -l) )); then
 print_info "Excellent performance (< 5s)"
 elif (( $(echo "$response_time < 15.0" | bc -l) )); then
 print_info "Good performance (< 15s)"
 else
 print_info "Slow response (> 15s) - consider model optimization"
 fi
else
 print_status 1 "Performance test failed"
fi

print_section "Test Summary"

echo "Ollama Integration Test Results:"
echo "--------------------------------"
echo " Service connectivity: PASS"
echo " Model availability: PASS" 
echo " Basic integration: PASS"
echo " Log processing: TESTED"
echo " Multi-format support: TESTED"
echo " Performance: MEASURED"

print_info "Integration testing complete!"
print_info "Logs saved to /tmp/ollama_test.log and /tmp/integration_test.log"

echo ""
echo " Next Steps:"
echo "1. Start the backend: uvicorn app.main:app --reload"
echo "2. Start the frontend: cd ../frontend && npm run dev"
echo "3. Test via web interface at http://localhost:3000"
echo ""
echo " For development:"
echo "- Test individual components with: python test_ollama_integration.py"
echo "- Test full pipeline with: python test_simple_integration.py"
echo "- Monitor Ollama: curl http://localhost:11434/api/tags"